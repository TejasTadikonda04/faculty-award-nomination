import pymupdf

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
    # Example usage
    pdf_file = "data/narayanan.pdf"
    print(extract_text_from_pdf(pdf_file))



"""
HOW TO USE:
from pdf_text_extractor import extract_text_from_pdf
text = extract_text_from_pdf("narayanan.pdf")
print(text)
"""