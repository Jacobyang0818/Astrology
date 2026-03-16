import fitz
from rapidocr_onnxruntime import RapidOCR
import numpy as np

def ocr_pdf(pdf_path, output_path):
    print(f"Starting OCR extraction for {pdf_path}...")
    ocr = RapidOCR()
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i in range(total_pages):
            page = doc[i]
            # render page to image
            pix = page.get_pixmap(dpi=150) # 150 dpi is usually enough for OCR
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            
            # if image has alpha, drop it
            if img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
                
            result, _ = ocr(img_array)
            
            f.write(f"\n--- PAGE {i+1} ---\n")
            if result:
                page_text = "\n".join([line[1] for line in result])
                f.write(page_text + "\n")
            else:
                f.write("\n")
                
            f.flush()
            if (i+1) % 10 == 0:
                print(f"Processed {i+1}/{total_pages} pages...")
                
    print(f"Finished OCR. Result saved to {output_path}")

if __name__ == "__main__":
    ocr_pdf("docs/astrology_guide_1.pdf", "docs/astrology_guide_1_ocr.txt")
