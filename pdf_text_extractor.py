import os
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

def convert_pdfs_to_txt(input_folder: str, output_folder: str):
    """
    Converts all PDFs in input_folder to text files in output_folder.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Iterate over all files in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_folder, filename)
            text = extract_text_from_pdf(pdf_path)

            # Save text to output folder with same name but .txt extension
            txt_filename = os.path.splitext(filename)[0] + ".txt"
            txt_path = os.path.join(output_folder, txt_filename)
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Converted {filename} -> {txt_filename}")


if __name__ == "__main__":
    input_folder = "data/CV"
    output_folder = "data/CVText"
    convert_pdfs_to_txt(input_folder, output_folder)
