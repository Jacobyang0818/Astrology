import os
from pypdf import PdfReader

def analyze_pdf(pdf_path, output_path, num_pages=15):
    try:
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"--- Analysis for {pdf_path} ---\n")
            f.write(f"Total Pages: {total_pages}\n\n")
            
            # Extract first few pages to see table of contents and structure
            for i in range(min(num_pages, total_pages)):
                page = reader.pages[i]
                text = page.extract_text()
                f.write(f"--- PAGE {i+1} ---\n")
                if text:
                    f.write(text + "\n\n")
                else:
                    f.write("[No text found on this page]\n\n")
                    
            # Extract a few pages from the middle to see typical content formatting
            mid_start = total_pages // 2
            f.write(f"\n--- MIDDLE PAGES SAMPLES (from page {mid_start}) ---\n")
            for i in range(mid_start, min(mid_start + 3, total_pages)):
                page = reader.pages[i]
                text = page.extract_text()
                f.write(f"--- PAGE {i+1} ---\n")
                if text:
                    f.write(text + "\n\n")
                else:
                    f.write("[No text found on this page]\n\n")
                    
        print(f"Analysis saved to {output_path}")
    except Exception as e:
        print(f"Error analyzing {pdf_path}: {e}")

if __name__ == "__main__":
    docs = ["docs/astrology_guide_1.pdf", "docs/astrology_guide_2.pdf"]
    for i, doc in enumerate(docs):
        if os.path.exists(doc):
            analyze_pdf(doc, f"docs/analysis_{i+1}.txt")
        else:
            print(f"{doc} not found.")
