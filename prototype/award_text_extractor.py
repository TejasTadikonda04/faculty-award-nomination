import pandas as pd
import os
from pathlib import Path

def extract_award_text():
    # define input and output paths
    input_dir = Path("./data/awards")
    output_dir = Path("./data/output")
    
    # create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # find excel file in input directory
    excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
    
    if not excel_files:
        print("no excel files found in input directory")
        return
    
    # use first excel file found
    excel_file = excel_files[0]
    
    # read excel file
    df = pd.read_excel(excel_file)
    
    # process each row
    for index, row in df.iterrows():
        # create filename from column b and column g
        # iloc is zero-indexed so column b is index 1 and column g is index 6
        col_b_value = str(row.iloc[1]).strip()
        col_g_value = str(row.iloc[6]).strip()
        
        # sanitize filename by removing invalid characters
        filename = f"{col_b_value}_{col_g_value}"
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            filename = filename.replace(char, "_")
        filename = f"{filename}.txt"
        
        # build formatted content
        content_lines = []
        for col_name, cell_value in row.items():
            content_lines.append(f"{col_name}:")
            content_lines.append(f"{cell_value}")
        
        content = "\n".join(content_lines)
        
        # write to text file
        output_path = output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"processed {len(df)} rows and created text files in {output_dir}")

if __name__ == "__main__":
    extract_award_text()