import os
import json
import pymupdf
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
CHUNK_SIZE = 300      # Number of words per chunk
CHUNK_OVERLAP = 50    # Overlap between chunks to preserve context
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2' # Standard, efficient embedding model

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts raw text from a PDF file using PyMuPDF.
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

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Splits text into overlapping chunks of words.
    """
    words = text.split()
    if not words:
        return []
    
    chunks = []
    # Slide a window across the list of words
    for i in range(0, len(words), chunk_size - overlap):
        # Create the chunk
        chunk_words = words[i : i + chunk_size]
        chunk_str = " ".join(chunk_words)
        
        # Only add non-empty chunks
        if chunk_str.strip():
            chunks.append(chunk_str)
            
        # Stop if we've reached the end
        if i + chunk_size >= len(words):
            break
            
    return chunks

def main():
    # 1. SETUP PATHS
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    cv_dir = project_root / "data" / "CV"
    output_dir = project_root / "data" / "output"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    faiss_index_path = output_dir / "cv_index.faiss"
    metadata_path = output_dir / "cv_metadata.json"

    # 2. DISCOVER FILES
    pdf_files = sorted(list(cv_dir.glob("*.pdf")))
    if not pdf_files:
        print(f"No PDF files found in {cv_dir}")
        return

    print(f"Found {len(pdf_files)} CVs. Loading embedding model ({MODEL_NAME})...")

    # 3. INITIALIZE MODEL
    model = SentenceTransformer(MODEL_NAME)
    
    # Lists to hold data before indexing
    all_embeddings = []
    metadata_store = {} # Maps ID (int) -> {filename, text_chunk}
    
    vector_id_counter = 0

    # 4. PROCESS FILES
    print("Processing files...")
    for pdf_file in pdf_files:
        print(f"  -> Parsing {pdf_file.name}")
        
        # Extract
        raw_text = extract_text_from_pdf(pdf_file)
        if not raw_text:
            continue
            
        # Chunk
        chunks = chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # Embed chunks (batch process per file for efficiency)
        if chunks:
            chunk_embeddings = model.encode(chunks)
            
            # Store
            for i, embedding in enumerate(chunk_embeddings):
                # Add to embeddings list
                all_embeddings.append(embedding)
                
                # Add to metadata store
                metadata_store[vector_id_counter] = {
                    "filename": pdf_file.name,
                    "chunk_id": i,
                    "text": chunks[i]
                }
                vector_id_counter += 1

    if not all_embeddings:
        print("No text extracted/embedded.")
        return

    # 5. CREATE & SAVE FAISS INDEX
    print(f"Building index with {len(all_embeddings)} vectors...")
    
    # Convert list to float32 numpy array (required by FAISS)
    embeddings_matrix = np.array(all_embeddings).astype('float32')
    
    # Get dimension from the embeddings (e.g., 384 for MiniLM)
    dimension = embeddings_matrix.shape[1]
    
    # Create Index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_matrix)
    
    # Persist Index
    faiss.write_index(index, str(faiss_index_path))
    
    # 6. SAVE METADATA
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_store, f, indent=2)

    print("\n--- Ingestion Complete ---")
    print(f"Saved FAISS index to: {faiss_index_path}")
    print(f"Saved Metadata to:    {metadata_path}")
    print(f"Total Chunks Indexed: {index.ntotal}")

if __name__ == "__main__":
    main()