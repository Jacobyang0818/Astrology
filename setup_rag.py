import os
import subprocess
import sys
import gdown
from dotenv import load_dotenv

def setup():
    print("=== Starting RAG Automated Setup ===")
    
    # 1. Load Environment
    load_dotenv()
    
    # 2. Ensure docs directory exists
    os.makedirs("docs", exist_ok=True)
    
    # 3. Download PDFs from Google Drive
    pdfs = {
        "docs/astrology_guide_1.pdf": "151KLdRjCkaCwW4eTppCitg8vcQFU_vfd",
        "docs/astrology_guide_2.pdf": "1nSwX_pPxoOLFOeVsR_Q8XFU_vfd"
    }
    
    for path, file_id in pdfs.items():
        if not os.path.exists(path):
            print(f"Downloading {path}...")
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, path, quiet=False)
        else:
            print(f"File already exists: {path}")

    # 4. Run OCR Extraction for Book 1
    # We use the logic from tests/ocr_extract.py
    ocr_out = "docs/astrology_guide_1_ocr.txt"
    if not os.path.exists(ocr_out):
        print("Running OCR extraction for Book 1...")
        try:
            # We import the function directly since we're in the same project
            # If not possible, we run it as a script
            from tests.ocr_extract import ocr_pdf
            ocr_pdf("docs/astrology_guide_1.pdf", ocr_out)
        except ImportError:
            print("Warning: Could not import ocr_pdf from tests.ocr_extract. Looking for file...")
            if os.path.exists("tests/ocr_extract.py"):
                subprocess.run([sys.executable, "tests/ocr_extract.py"], check=True)
            else:
                print("Error: OCR script not found.")
                return
    else:
        print(f"OCR result already exists: {ocr_out}")

    # 5. Build Vector Database
    print("Building Vector Database (indexing)...")
    if os.path.exists("build_rag.py"):
        subprocess.run([sys.executable, "build_rag.py"], check=True)
    else:
        print("Error: build_rag.py not found.")

    print("=== RAG Setup Completed Successfully ===")

if __name__ == "__main__":
    setup()
