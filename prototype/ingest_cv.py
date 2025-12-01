import os
import json
import pymupdf
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Configuration
CHUNK_SIZE = 300      # Words per chunk
CHUNK_OVERLAP = 50    # Context overlap
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2' # Embedding model

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text using pymupdf.
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
    Split text into overlapping chunks.
    """
    words = text.split()
    if not words:
        return []
    
    chunks = []
    # Sliding window loop
    for i in range(0, len(words), chunk_size - overlap):
        # Build string
        chunk_words = words[i : i + chunk_size]
        chunk_str = " ".join(chunk_words)
        
        # Skip empty
        if chunk_str.strip():
            chunks.append(chunk_str)
            
        # Check bounds
        if i + chunk_size >= len(words):
            break
            
    return chunks

def main():
    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    cv_dir = project_root / "data" / "CV"
    output_dir = project_root / "data" / "output"
    
    # Make output dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    faiss_index_path = output_dir / "cv_index.faiss"
    metadata_path = output_dir / "cv_metadata.json"

    # Find pdf files
    pdf_files = sorted(list(cv_dir.glob("*.pdf")))
    if not pdf_files:
        print(f"No PDF files found in {cv_dir}")
        return

    print(f"Found {len(pdf_files)} CVs. Loading embedding model ({MODEL_NAME})...")

    # Load model
    model = SentenceTransformer(MODEL_NAME)
    
    # Temp buffers
    all_embeddings = []
    metadata_store = {} # Map id to info
    
    vector_id_counter = 0

    # Process files
    print("Processing files...")
    for pdf_file in pdf_files:
        print(f"   -> Parsing {pdf_file.name}")
        
        # Get text
        raw_text = extract_text_from_pdf(pdf_file)
        if not raw_text:
            continue
            
        # Chunk text
        chunks = chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # Get embeddings
        if chunks:
            chunk_embeddings = model.encode(chunks)
            
            # Save results
            for i, embedding in enumerate(chunk_embeddings):
                # Append vector
                all_embeddings.append(embedding)
                
                # Store metadata
                metadata_store[vector_id_counter] = {
                    "filename": pdf_file.name,
                    "chunk_id": i,
                    "text": chunks[i]
                }
                vector_id_counter += 1

    if not all_embeddings:
        print("No text extracted/embedded.")
        return

    # Build index
    print(f"Building index with {len(all_embeddings)} vectors...")
    
    # Convert to float32
    embeddings_matrix = np.array(all_embeddings).astype('float32')
    
    # Get dimension
    dimension = embeddings_matrix.shape[1]
    
    # Create index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_matrix)
    
    # Save index
    faiss.write_index(index, str(faiss_index_path))
    
    # Save metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_store, f, indent=2)

    print("\n--- Ingestion Complete ---")
    print(f"Saved FAISS index to: {faiss_index_path}")
    print(f"Saved Metadata to:    {metadata_path}")
    print(f"Total Chunks Indexed: {index.ntotal}")

if __name__ == "__main__":
    main()