import os
import time
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

load_dotenv()
if "GEMINI_API_KEY" not in os.environ:
    print("Error: GEMINI_API_KEY not found in environment.")
    exit(1)

os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# ─── 讀取 RAG 模式設定 ────────────────────────────────────────────────────────
RAG_MODE = os.getenv("RAG_MODE", "simple").strip().lower()
if RAG_MODE not in ("simple", "parent"):
    print(f"Warning: Unknown RAG_MODE='{RAG_MODE}'. Falling back to 'simple'.")
    RAG_MODE = "simple"
print(f">>> RAG_MODE is set to: '{RAG_MODE}'")


def load_docs() -> list:
    """Load source documents from docs/ directory."""
    docs = []
    file_1 = "docs/astrology_guide_1_ocr.txt"
    if os.path.exists(file_1):
        print(f"Loading {file_1}...")
        loader1 = TextLoader(file_1, encoding="utf-8")
        docs.extend(loader1.load())
    else:
        print(f"Warning: {file_1} not found, skipping Book 1.")

    file_2 = "docs/astrology_guide_2.pdf"
    if os.path.exists(file_2):
        print(f"Loading {file_2}...")
        loader2 = PyPDFLoader(file_2)
        docs.extend(loader2.load())
    else:
        print(f"Warning: {file_2} not found, skipping Book 2.")

    return docs


def init_qdrant(embeddings: GoogleGenerativeAIEmbeddings) -> QdrantVectorStore:
    """Initialize (or reset) the Qdrant collection and return a VectorStore."""
    test_vec = embeddings.embed_query("test")
    dim = len(test_vec)
    print(f"DEBUG: Embedding dimension is {dim}")

    client = QdrantClient(path="./qdrant_db")
    if client.collection_exists(collection_name="astrology_knowledge"):
        print("Deleting existing collection to ensure correct dimensions...")
        client.delete_collection(collection_name="astrology_knowledge")

    client.create_collection(
        collection_name="astrology_knowledge",
        vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE)
    )

    return QdrantVectorStore(
        client=client,
        collection_name="astrology_knowledge",
        embedding=embeddings
    )


def build_simple(docs: list, qdrant: QdrantVectorStore):
    """
    Simple chunking mode (字數切割):
    - 快速、API 用量低
    - chunk_size=700, overlap=150
    """
    print("\n--- [simple mode] Splitting with RecursiveCharacterTextSplitter ---")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    splits = splitter.split_documents(docs)
    print(f"Created {len(splits)} chunks.")

    batch_size = 50
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i + batch_size]
        print(f"Processing batch {i+1}~{min(i+batch_size, len(splits))} / {len(splits)}...")
        try:
            qdrant.add_documents(batch)
        except Exception as e:
            if "429" in str(e):
                print("Rate limit hit. Sleeping for 80 seconds...")
                time.sleep(80)
                qdrant.add_documents(batch)
            else:
                raise e

        if i + batch_size < len(splits):
            print("Sleeping 15s (Gemini free tier rate limit)...")
            time.sleep(15)

    print("✅ [simple] Vector database built at ./qdrant_db")


def build_parent(docs: list, qdrant: QdrantVectorStore):
    """
    Parent Document Retriever mode (父子文獻):
    - 檢索精準、AI 回答上下文豐富
    - 需要更多 API 請求時間與本機存儲 (./docstore/parents.json)
    """
    try:
        from langchain.retrievers import ParentDocumentRetriever
    except ImportError:
        from langchain_classic.retrievers import ParentDocumentRetriever

    from app.utils.store import PersistentInMemoryStore

    print("\n--- [parent mode] Setting up ParentDocumentRetriever ---")
    os.makedirs("./docstore", exist_ok=True)
    store = PersistentInMemoryStore("./docstore/parents.json")

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

    retriever = ParentDocumentRetriever(
        vectorstore=qdrant,
        docstore=store,
        child_splitter=child_splitter,
        parent_splitter=parent_splitter,
    )

    # batch_size=1 to avoid hitting 100 req/min free tier limit
    batch_size = 1
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        print(f"Processing parent doc {i+1} / {len(docs)}...")
        try:
            retriever.add_documents(batch)
            print(f"  ✓ Done. Sleeping 30s to respect rate limit...")
            time.sleep(30)
        except Exception as e:
            if "429" in str(e):
                print("  Rate limit hit. Sleeping for 90 seconds...")
                time.sleep(90)
                retriever.add_documents(batch)
            else:
                raise e

    print("✅ [parent] Database built at ./qdrant_db + ./docstore/parents.json")


def build_vector_db():
    print("Loading documents...")
    docs = load_docs()
    if not docs:
        print("No documents loaded. Exiting.")
        return

    print("Initializing Gemini Embedding model...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    print("Building Qdrant Vector Store locally...")
    qdrant = init_qdrant(embeddings)

    if RAG_MODE == "parent":
        build_parent(docs, qdrant)
    else:
        build_simple(docs, qdrant)


if __name__ == "__main__":
    build_vector_db()
