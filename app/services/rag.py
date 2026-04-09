import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

_retriever = None


def _get_rag_mode() -> str:
    mode = os.getenv("RAG_MODE", "simple").strip().lower()
    if mode not in ("simple", "parent"):
        logger.warning(f"Unknown RAG_MODE='{mode}'. Falling back to 'simple'.")
        return "simple"
    return mode


def _build_simple_retriever(vector_store: QdrantVectorStore):
    """
    Simple mode: 直接用 VectorStore 當 retriever (字數切割)。
    呼叫 .invoke() 時回傳 Child chunks (700字/塊)。
    """
    return vector_store.as_retriever(search_kwargs={"k": 8})


def _build_parent_retriever(vector_store: QdrantVectorStore):
    """
    Parent mode: 用 ParentDocumentRetriever，
    用小塊做向量配對後，回傳完整大塊（1500字）給 LLM。
    """
    try:
        from langchain.retrievers import ParentDocumentRetriever
    except ImportError:
        from langchain_classic.retrievers import ParentDocumentRetriever

    from app.utils.store import PersistentInMemoryStore

    docstore_path = "./docstore/parents.json"
    if not os.path.exists(docstore_path):
        logger.warning(
            f"Parent docstore not found at '{docstore_path}'. "
            "Did you run 'python build_rag.py' with RAG_MODE=parent? Falling back to simple mode."
        )
        return _build_simple_retriever(vector_store)

    store = PersistentInMemoryStore(docstore_path)

    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )

    return ParentDocumentRetriever(
        vectorstore=vector_store,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
        search_kwargs={"k": 5}
    )


def get_retriever(gemini_enabled: bool):
    global _retriever
    if _retriever is not None:
        return _retriever

    db_path = "./qdrant_db"
    if not os.path.exists(db_path):
        logger.info(f"Qdrant DB not found at '{db_path}'. RAG will be skipped.")
        return None

    if not gemini_enabled:
        logger.info("Gemini API key not configured. RAG will be skipped.")
        return None

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        client = QdrantClient(path=db_path)

        collections = client.get_collections().collections
        if "astrology_knowledge" not in [c.name for c in collections]:
            logger.warning("Qdrant collection 'astrology_knowledge' not found. RAG will be skipped.")
            return None

        vector_store = QdrantVectorStore(
            client=client,
            collection_name="astrology_knowledge",
            embedding=embeddings
        )

        rag_mode = _get_rag_mode()
        logger.info(f"RAG mode: '{rag_mode}'")

        if rag_mode == "parent":
            _retriever = _build_parent_retriever(vector_store)
            logger.info("Parent Document RAG retriever initialized successfully.")
        else:
            _retriever = _build_simple_retriever(vector_store)
            logger.info("Simple RAG retriever initialized successfully.")

        return _retriever

    except Exception as e:
        logger.error(f"RAG Initialization failed: {e}", exc_info=True)
        return None
