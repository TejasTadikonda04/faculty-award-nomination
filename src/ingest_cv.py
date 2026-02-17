"""
CV Ingestion Pipeline
Extracts text from faculty CVs, chunks them, generates embeddings, and stores in Pinecone.
"""
import sys
import pymupdf
from pathlib import Path
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from tqdm import tqdm
import hashlib

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from config import (
    CV_DIR,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
    EMBEDDING_MODEL_NAME,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    validate_config
)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text from a PDF file using PyMuPDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    text_content = []
    try:
        doc = pymupdf.open(pdf_path)
        for page in doc:
            text_content.append(page.get_text())
        doc.close()
        return "\n".join(text_content)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Number of words per chunk
        overlap: Number of overlapping words between chunks
        
    Returns:
        List of text chunks
    """
    words = text.split()
    if not words:
        return []
    
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i : i + chunk_size]
        chunk_str = " ".join(chunk_words)
        
        if chunk_str.strip():
            chunks.append(chunk_str)
            
        if i + chunk_size >= len(words):
            break
            
    return chunks


def generate_chunk_id(filename: str, chunk_index: int) -> str:
    """
    Generate a unique, deterministic ID for a chunk.
    
    Args:
        filename: Source PDF filename
        chunk_index: Index of the chunk
        
    Returns:
        Unique chunk ID
    """
    id_string = f"{filename}_{chunk_index}"
    return hashlib.md5(id_string.encode()).hexdigest()


def ingest_cvs():
    """
    Main ingestion pipeline:
    1. Extract text from all CVs
    2. Chunk the text
    3. Generate embeddings
    4. Upload to Pinecone
    """
    # Validate configuration
    try:
        validate_config()
    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}")
        return
    
    # Find PDF files
    pdf_files = sorted(list(CV_DIR.glob("*.pdf")))
    if not pdf_files:
        print(f"No PDF files found in {CV_DIR}")
        return
    
    print(f"Found {len(pdf_files)} CVs")
    
    # Initialize Pinecone
    print("Connecting to Pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    
    # Load embedding model
    print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Process each CV
    total_chunks = 0
    
    for pdf_file in tqdm(pdf_files, desc="Processing CVs"):
        print(f"\n  -> Processing {pdf_file.name}")
        
        # Extract text
        raw_text = extract_text_from_pdf(pdf_file)
        if not raw_text:
            print(f"    ! No text extracted from {pdf_file.name}")
            continue
        
        # Chunk text
        chunks = chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
        if not chunks:
            print(f"    ! No chunks created from {pdf_file.name}")
            continue
        
        print(f"    Created {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = model.encode(chunks, show_progress_bar=False)
        
        # Prepare vectors for Pinecone
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = generate_chunk_id(pdf_file.name, i)
            
            vectors.append({
                "id": vector_id,
                "values": embedding.tolist(),
                "metadata": {
                    "filename": pdf_file.name,
                    "chunk_id": i,
                    "text": chunk[:1000],  # Pinecone metadata limit is ~40KB, truncate long chunks
                    "faculty_name": pdf_file.stem  # Use filename without extension as faculty identifier
                }
            })
        
        # Upload to Pinecone in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            index.upsert(vectors=batch, namespace=PINECONE_NAMESPACE)
        
        total_chunks += len(chunks)
        print(f"    [OK] Uploaded {len(chunks)} vectors to Pinecone")
    
    # Get index stats
    stats = index.describe_index_stats()
    
    print("\n" + "="*50)
    print("[SUCCESS] INGESTION COMPLETE")
    print("="*50)
    print(f"Total CVs processed: {len(pdf_files)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Pinecone index stats:")
    print(f"  - Total vectors: {stats.get('total_vector_count', 'N/A')}")
    print(f"  - Namespace '{PINECONE_NAMESPACE}': {stats.get('namespaces', {}).get(PINECONE_NAMESPACE, {}).get('vector_count', 'N/A')} vectors")
    print("="*50)


if __name__ == "__main__":
    ingest_cvs()
