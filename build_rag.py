import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models
import time

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

    try:
        from langchain.retrievers import ParentDocumentRetriever
    except ImportError:
        from langchain_classic.retrievers import ParentDocumentRetriever

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from app.utils.store import PersistentInMemoryStore

    # 1. 建立 DocStore (供 Parent Documents 本機儲存，直接存成 json 避免模組依賴錯誤)
    print("Setting up DocStore for Parent Documents...")
    store = PersistentInMemoryStore("./docstore/parents.json")
    
    # 2. 定義切塊策略 (Splitting Strategy)
    print("Setting up splitters...")
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
    
    import time
    batch_size = 2 # 縮小批次，因為每個 Parent 裡面包含了很多個 Child
    
    print("Adding documents to ParentDocumentRetriever (VectorDB + DocStore)...")
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        print(f"Processing parent batch {i+1} to {min(i+batch_size, len(docs))} of {len(docs)}...")
        try:
            retriever.add_documents(batch)
            print(f"成功處理第 {i} 到 {i+batch_size} 份文件")
            # 關鍵：每處理一小批就強制休息，避開每分鐘 100 次的限制
            time.sleep(20)
        except Exception as e:
            if "429" in str(e):
                print("觸發限流，強制休息 80 秒...")
                time.sleep(80)
                retriever.add_documents(batch) # 重試
            else:
                raise e
            
            
            
        if i + batch_size < len(docs):
            print("Sleeping for 15 seconds to respect Gemini Free Tier API rate limits...")
            time.sleep(15)
    
    print("ParentDocumentRetriever database built successfully at ./qdrant_db and ./docstore!")

if __name__ == "__main__":
    build_vector_db()
