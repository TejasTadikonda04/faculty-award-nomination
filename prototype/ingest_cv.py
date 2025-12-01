import pymupdf
import pandas as pd
from pathlib import Path

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts and returns all text from a given PDF file.
    """
    text_content = []
    try:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            text_content.append(page.get_text())
        return "\n".join(text_content)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

if __name__ == "__main__":
    # Define paths
    cv_dir = Path("data/CV")
    output_dir = Path("data/output")
    output_file = output_dir / "cv_data.csv"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files
    pdf_files = sorted(cv_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in data/CV/")
        exit()

    # Data collection list
    data = []

    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        text = extract_text_from_pdf(str(pdf_file))
        
        # Only add if text was actually extracted
        if text.strip():
            data.append({
                "filename": pdf_file.name,
                "text": text
            })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    
    print(f"\nProcessed {len(df)} PDFs.")
    print(f"Data saved to: {output_file}")