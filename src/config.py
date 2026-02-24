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
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
TAMU_API_KEY = os.getenv("TAMU_API_KEY")
TAMU_API_BASE = os.getenv("TAMU_API_BASE", "https://chat-api.tamu.ai/api")

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

# LLM Configuration - TAMU AI Chat
TAMU_MODEL = "protected.gemini-2.0-flash-lite"  # Fast, cheap, good quality
# Alternative TAMU models:
# - "protected.Claude 3.5 Sonnet" (highest quality)
# - "protected.Claude Sonnet 4" (newest Claude)
# - "protected.gpt-4o" (OpenAI's best)
# - "protected.gemini-2.5-flash" (Google's fast model)
# - "protected.gemini-2.5-pro" (Google's best)

# Validation
def validate_config():
    """Validate that required configuration is present."""
    missing = []
    
    if not TAMU_API_KEY:
        missing.append("TAMU_API_KEY")
    if not PINECONE_API_KEY:
        missing.append("PINECONE_API_KEY")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    if not CV_DIR.exists():
        raise FileNotFoundError(f"CV directory not found: {CV_DIR}")
    
    return True
