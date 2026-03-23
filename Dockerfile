# Faculty Award Nomination System - RAG-based faculty-award matching
# Python 3.11 for compatibility with sentence-transformers, torch, etc.
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PyMuPDF and scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    mupdf-tools \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/

# Create data directory structure (users mount volumes at runtime)
RUN mkdir -p data/cv data/awards data/output

# Set Python path so imports work from project root
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default: run RAG matching (can be overridden)
# Use: docker run ... match | ingest | extract
ENTRYPOINT ["python", "-m"]
CMD ["src.rag_matching"]
