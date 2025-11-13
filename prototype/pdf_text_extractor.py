import pymupdf
from pathlib import Path

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts and returns all text from a given PDF file.
    """
    text_content = []
    doc = pymupdf.open(pdf_path)
    for page in doc:
        text_content.append(page.get_text())

    return "\n".join(text_content)


if __name__ == "__main__":
    # Process all PDFs in data/CV/
    cv_dir = Path("data/CV")
    output_dir = Path("data/output")
    output_file = output_dir / "cv_text.txt"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all PDF files
    pdf_files = sorted(cv_dir.glob("*.pdf"))
    
    # Extract and concatenate text from all PDFs
    all_text = []
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file.name}...")
        text = extract_text_from_pdf(str(pdf_file))
        all_text.append(f"\n\n{'='*80}\n")
        all_text.append(f"FILE: {pdf_file.name}\n")
        all_text.append(f"{'='*80}\n\n")
        all_text.append(text)
    
    # Write to output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("".join(all_text))
    
    print(f"\nExtracted text from {len(pdf_files)} PDFs and saved to {output_file}")