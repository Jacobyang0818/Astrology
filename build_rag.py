import os
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

def build_vector_db():
    print("Loading documents...")
    docs = []
    
    # 1. Load OCR'd Text from Book 1
    file_1 = "docs/astrology_guide_1_ocr.txt"
    if os.path.exists(file_1):
        print(f"Loading {file_1}...")
        loader1 = TextLoader(file_1, encoding="utf-8")
        docs.extend(loader1.load())
    else:
        print(f"Warning: {file_1} not found, skipping Book 1.")
        
    # 2. Load PDF from Book 2
    file_2 = "docs/astrology_guide_2.pdf"
    if os.path.exists(file_2):
        print(f"Loading {file_2}...")
        loader2 = PyPDFLoader(file_2)
        docs.extend(loader2.load())
    else:
        print(f"Warning: {file_2} not found, skipping Book 2.")

    if not docs:
        print("No documents loaded. Exiting.")
        return

    print("Splitting texts...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150,
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    splits = text_splitter.split_documents(docs)
    print(f"Created {len(splits)} chunks.")

    print("Initializing Google Generative AI Embeddings (Stable model)...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # 測試維度
    test_vec = embeddings.embed_query("test")
    dim = len(test_vec)
    print(f"DEBUG: Embedding dimension is {dim}")

    print("Building Qdrant Vector Store locally...")
    # Use disk-based Qdrant client
    client = QdrantClient(path="./qdrant_db")
    
    if client.collection_exists(collection_name="astrology_knowledge"):
        print("Deleting existing collection to ensure correct dimensions...")
        client.delete_collection(collection_name="astrology_knowledge")
        
    client.create_collection(
        collection_name="astrology_knowledge",
        vectors_config=models.VectorParams(
            size=dim,  # 使用實際測得的維度
            distance=models.Distance.COSINE
        )
    )
    
    qdrant = QdrantVectorStore(
        client=client,
        collection_name="astrology_knowledge",
        embedding=embeddings
    )
    
    import time
    batch_size = 50
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i + batch_size]
        print(f"Processing batch {i+1} to {min(i+batch_size, len(splits))} of {len(splits)}...")
        try:
            qdrant.add_documents(batch)
        except Exception as e:
            print(f"Rate limit hit during batch. Sleeping for 60 seconds... error: {e}")
            time.sleep(60)
            qdrant.add_documents(batch)
            
        if i + batch_size < len(splits):
            print("Sleeping for 15 seconds to respect Gemini Free Tier API rate limits...")
            time.sleep(15)
    
    print("Vector database built successfully at ./qdrant_db!")

if __name__ == "__main__":
    build_vector_db()
