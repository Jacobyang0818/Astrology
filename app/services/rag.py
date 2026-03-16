import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)

_qdrant_vector_store = None

def get_retriever(gemini_enabled: bool):
    global _qdrant_vector_store
    if _qdrant_vector_store is not None:
        return _qdrant_vector_store

    db_path = "./qdrant_db"
    if not os.path.exists(db_path):
        logger.info(f"Qdrant DB path not found: {db_path}. RAG will be skipped.")
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

        _qdrant_vector_store = QdrantVectorStore(
            client=client,
            collection_name="astrology_knowledge",
            embedding=embeddings
        )
        logger.info("Qdrant RAG retriever initialized successfully.")
        return _qdrant_vector_store
    except Exception as e:
        logger.error(f"RAG Initialization failed: {e}", exc_info=True)
        return None
