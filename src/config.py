"""
Configuration settings for the Faculty Award Nomination System.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CV_DIR = DATA_DIR / "cv"
AWARDS_DIR = DATA_DIR / "awards"
OUTPUT_DIR = DATA_DIR / "output"
PROMPTS_DIR = Path(__file__).parent / "prompts"

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
TAMU_API_KEY = os.getenv("TAMU_API_KEY")

# Pinecone Configuration
PINECONE_INDEX_NAME = "faculty-cv-embeddings"
PINECONE_NAMESPACE = "isen-faculty"  # Use namespaces to organize different departments

# Embedding Configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Text Processing Configuration
CHUNK_SIZE = 300  # Words per chunk
CHUNK_OVERLAP = 50  # Words of overlap between chunks

# RAG Configuration
TOP_K_CHUNKS = 10  # Number of chunks to retrieve for context

# LLM Configuration
LLM_MODEL = "google/gemini-flash-1.5"  # OpenRouter model (fast and free)
LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Validation
def validate_config():
    """Validate that required configuration is present."""
    missing = []
    
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not PINECONE_API_KEY:
        missing.append("PINECONE_API_KEY")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    if not CV_DIR.exists():
        raise FileNotFoundError(f"CV directory not found: {CV_DIR}")
    
    return True
