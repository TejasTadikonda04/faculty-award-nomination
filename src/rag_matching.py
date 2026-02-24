"""
RAG-based Faculty-Award Matching
Retrieves relevant CV chunks from Pinecone and uses LLM to rank faculty qualification.
"""
import sys
import requests
from pathlib import Path
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from config import (
    OUTPUT_DIR,
    PROMPTS_DIR,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_NAMESPACE,
    EMBEDDING_MODEL_NAME,
    TOP_K_CHUNKS,
    TAMU_API_KEY,
    TAMU_API_BASE,
    TAMU_MODEL,
    validate_config
)


def load_pinecone_index():
    """
    Connect to Pinecone index.
    
    Returns:
        Pinecone index object
    """
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    return index


def get_relevant_context(award_text: str, index, model, k: int = TOP_K_CHUNKS) -> tuple[str, list[str]]:
    """
    Embed award text and retrieve relevant CV chunks from Pinecone.
    
    Args:
        award_text: Award description text
        index: Pinecone index
        model: SentenceTransformer model
        k: Number of chunks to retrieve
        
    Returns:
        Tuple of (formatted context string, list of matched faculty names)
    """
    print("Embedding award text and searching Pinecone...")
    
    # Generate query embedding
    query_embedding = model.encode([award_text])[0].tolist()
    
    # Search Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=k,
        namespace=PINECONE_NAMESPACE,
        include_metadata=True
    )
    
    # Group results by faculty
    hits_by_faculty = {}
    
    for match in results['matches']:
        metadata = match['metadata']
        faculty_name = metadata.get('faculty_name', metadata.get('filename', 'Unknown'))
        text_chunk = metadata.get('text', '')
        score = match['score']
        
        if faculty_name not in hits_by_faculty:
            hits_by_faculty[faculty_name] = []
        
        hits_by_faculty[faculty_name].append({
            'text': text_chunk,
            'score': score
        })
    
    # Format context for prompt
    context_str = ""
    for faculty_name, chunks in hits_by_faculty.items():
        context_str += f"### CANDIDATE: {faculty_name}\n"
        context_str += "RELEVANT EXCERPTS:\n"
        for i, chunk_data in enumerate(chunks, 1):
            context_str += f"...{chunk_data['text']}...\n"
        context_str += "\n"
    
    faculty_names = list(hits_by_faculty.keys())
    
    return context_str, faculty_names


def call_llm(prompt: str) -> str:
    """
    Call TAMU AI Chat API with the constructed prompt.
    
    Args:
        prompt: Full prompt text
        
    Returns:
        LLM response text
    """
    print(f"Calling TAMU AI Chat ({TAMU_MODEL})...")
    
    response = requests.post(
        f"{TAMU_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {TAMU_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": TAMU_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False  # Disable streaming to get JSON response
        },
        timeout=60  # Increase timeout for longer responses
    )
    
    data = response.json()
    
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    else:
        raise Exception(f"TAMU API error: {data}")


def match_award_to_faculty(award_file_path: Path, prompt_template_path: Path = None) -> str:
    """
    Main RAG pipeline: Match an award to qualified faculty.
    
    Args:
        award_file_path: Path to award description text file
        prompt_template_path: Optional path to custom prompt template
        
    Returns:
        LLM evaluation result
    """
    # Validate configuration
    try:
        validate_config()
    except (ValueError, FileNotFoundError) as e:
        print(f"Configuration error: {e}")
        return ""
    
    # Load prompt template
    if prompt_template_path is None:
        prompt_template_path = PROMPTS_DIR / "award_to_cvs_prompt.md"
    
    if not prompt_template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {prompt_template_path}")
    
    with open(prompt_template_path, "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
    
    # Load award text
    print(f"Reading award: {award_file_path.name}")
    with open(award_file_path, "r", encoding="utf-8") as f:
        award_text = f.read()
    
    # Load resources
    print("Loading Pinecone index and embedding model...")
    index = load_pinecone_index()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    # Retrieve relevant context
    context_string, matched_faculty = get_relevant_context(award_text, index, model)
    
    print(f"Found relevant matches from: {matched_faculty}")
    
    # Construct final prompt
    final_prompt = prompt_template.replace("{AWARD_TEXT}", award_text).replace("{CV_TEXT}", context_string)
    
    # Call LLM
    result = call_llm(final_prompt)
    
    return result


def main():
    """
    Example usage: Match a specific award to faculty.
    """
    # Example: Match "Research Excellence" award
    award_file = OUTPUT_DIR / "5.02_Research Excellence.txt"
    
    if not award_file.exists():
        print(f"Award file not found: {award_file}")
        print("Run award_text_extractor.py first to extract awards from Excel.")
        return
    
    print("="*60)
    print("RAG-BASED FACULTY-AWARD MATCHING")
    print("="*60)
    
    result = match_award_to_faculty(award_file)
    
    print("\n" + "="*60)
    print("MATCHING RESULTS")
    print("="*60)
    print(result)
    print("="*60)


if __name__ == "__main__":
    main()
