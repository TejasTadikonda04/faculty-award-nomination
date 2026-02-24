"""
Award Text Extractor
Extracts award descriptions from Excel database and saves as individual text files.
"""
import sys
import pandas as pd
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from config import AWARDS_DIR, OUTPUT_DIR


def extract_award_text():
    """
    Extract award information from Excel database and save as text files.
    Each row becomes a separate file named: {Column_B}_{Column_G}.txt
    """
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find Excel file
    excel_files = list(AWARDS_DIR.glob("*.xlsx")) + list(AWARDS_DIR.glob("*.xls"))
    
    if not excel_files:
        print(f"No Excel files found in {AWARDS_DIR}")
        return
    
    # Use first Excel file found
    excel_file = excel_files[0]
    print(f"Reading awards from: {excel_file.name}")
    
    # Read Excel file
    df = pd.read_excel(excel_file)
    
    print(f"Found {len(df)} awards")
    
    # Process each row
    for index, row in df.iterrows():
        # Create filename from column B and column G
        # iloc is zero-indexed so column B is index 1 and column G is index 6
        col_b_value = str(row.iloc[1]).strip()
        col_g_value = str(row.iloc[6]).strip()
        
        # Sanitize filename by removing invalid characters
        filename = f"{col_b_value}_{col_g_value}"
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        filename = f"{filename}.txt"
        
        # Build formatted content
        content_lines = []
        for col_name, cell_value in row.items():
            content_lines.append(f"{col_name}:")
            content_lines.append(f"{cell_value}")
        
        content = "\n".join(content_lines)
        
        # Write to text file
        output_path = OUTPUT_DIR / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"[OK] Processed {len(df)} awards -> {OUTPUT_DIR}")


if __name__ == "__main__":
    extract_award_text()
