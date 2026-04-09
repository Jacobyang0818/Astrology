import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils.store import PersistentInMemoryStore

try:
    from langchain.retrievers import ParentDocumentRetriever
except ImportError:
    from langchain_classic.retrievers import ParentDocumentRetriever

logger = logging.getLogger(__name__)

_retriever = None

def get_retriever(gemini_enabled: bool):
    global _retriever
    if _retriever is not None:
        return _retriever

    db_path = "./qdrant_db"
    docstore_path = "./docstore/parents.json"
    if not os.path.exists(db_path) or not os.path.exists(docstore_path):
        logger.info(f"RAG DB path not found: {db_path} or {docstore_path}. RAG will be skipped.")
        return None

    if not gemini_enabled:
        logger.info("Gemini API key not configured. RAG will be skipped.")
        return None

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        client = QdrantClient(path=db_path)
        
        # Check if collection exists
        collections = client.get_collections().collections
        if "astrology_knowledge" not in [c.name for c in collections]:
            logger.warning(f"Qdrant collection 'astrology_knowledge' not found. RAG will be skipped.")
            return None

        vector_store = QdrantVectorStore(
            client=client,
            collection_name="astrology_knowledge",
            embedding=embeddings
        )
        
        store = LocalFileStore(docstore_path)
        
        # Splitter configurations must match build_rag.py
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

        _retriever = ParentDocumentRetriever(
            vectorstore=vector_store,
            docstore=store,
            child_splitter=child_splitter,
            parent_splitter=parent_splitter,
            search_kwargs={"k": 5} # Fetch up to 5 large parent contexts
        )
        
        logger.info("Parent Document RAG retriever initialized successfully.")
        return _retriever
    except Exception as e:
        logger.error(f"RAG Initialization failed: {e}", exc_info=True)
        return None
