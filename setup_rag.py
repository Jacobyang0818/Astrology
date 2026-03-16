import os
import subprocess
import sys
import gdown
import time
from dotenv import load_dotenv

def download_file(path, file_id):
    if os.path.exists(path):
        print(f"File already exists: {path}")
        return True
    
    print(f"Attempting to download {path} (ID: {file_id})...")
    for attempt in range(1, 4):
        try:
            print(f"Attempt {attempt}...")
            # Try with fuzzy=True and direct id
            gdown.download(id=file_id, output=path, quiet=False, fuzzy=True)
            if os.path.exists(path):
                print(f"Successfully downloaded {path}")
                return True
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            time.sleep(5)
    
    print(f"Final attempt for {path} using URL fallback...")
    try:
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url=url, output=path, quiet=False)
        return os.path.exists(path)
    except:
        return False

def setup():
    print("=== Starting RAG Automated Setup ===")
    load_dotenv()
    os.makedirs("docs", exist_ok=True)
    
    pdfs = {
        "docs/astrology_guide_1.pdf": "151KLdRjCkaCwW4eTppCitg8vcQFU_vfd",
        "docs/astrology_guide_2.pdf": "1nSwX_pPxoOLFOeVsR_Q8XFU_vfd"
    }
    
    for path, file_id in pdfs.items():
        download_file(path, file_id)

    # 4. Run OCR Extraction for Book 1
    ocr_out = "docs/astrology_guide_1_ocr.txt"
    if not os.path.exists(ocr_out):
        if os.path.exists("docs/astrology_guide_1.pdf"):
            print("Running OCR extraction for Book 1...")
            try:
                # Try import first
                try:
                    from tests.ocr_extract import ocr_pdf
                    ocr_pdf("docs/astrology_guide_1.pdf", ocr_out)
                except (ImportError, ModuleNotFoundError):
                    print("Running OCR as subprocess...")
                    subprocess.run([sys.executable, "tests/ocr_extract.py"], check=True)
            except Exception as e:
                print(f"OCR failed: {e}")
        else:
            print("Skipping OCR: astrology_guide_1.pdf missing.")
    else:
        print(f"OCR result already exists: {ocr_out}")

    # 5. Build Vector Database
    print("Building Vector Database (indexing)...")
    try:
        if os.path.exists("build_rag.py"):
            subprocess.run([sys.executable, "build_rag.py"], check=True)
        else:
            print("Error: build_rag.py not found.")
    except Exception as e:
        print(f"Indexing failed: {e}")

    print("=== RAG Setup Process Finished ===")

if __name__ == "__main__":
    setup()

if __name__ == "__main__":
    setup()
