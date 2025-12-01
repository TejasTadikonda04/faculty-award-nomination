import os
import json
import faiss
import requests
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# --- CONFIGURATION ---
TOP_K_CHUNKS = 10  # Number of relevant chunks to retrieve
MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'

def load_resources(output_dir: Path):
    """
    Loads the FAISS index and metadata JSON.
    """
    faiss_path = output_dir / "cv_index.faiss"
    metadata_path = output_dir / "cv_metadata.json"

    if not faiss_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Index or Metadata not found. Run ingest_cv.py first.")

    print("Loading FAISS index and metadata...")
    index = faiss.read_index(str(faiss_path))
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
        # Convert keys to integers for easier lookup later
        metadata = {int(k): v for k, v in metadata.items()}

    return index, metadata

def get_relevant_context(award_text: str, index, metadata, model, k: int) -> str:
    """
    Embeds the award text, searches the index, and formats the results.
    """
    print("Embedding award text and searching index...")
    
    # 1. Embed the query (Award Text)
    query_embedding = model.encode([award_text])
    query_embedding = np.array(query_embedding).astype('float32')

    # 2. Search FAISS
    # distances: how close the match is (smaller is better for L2)
    # indices: the IDs of the matching vectors
    distances, indices = index.search(query_embedding, k)
    
    # 3. Retrieve and Organize Hits
    # We want to group chunks by professor so the LLM gets a coherent view
    hits_by_professor = {}
    
    for idx in indices[0]:
        if idx == -1: continue # FAISS returns -1 if not enough neighbors found
        
        record = metadata.get(idx)
        if record:
            filename = record['filename']
            text_chunk = record['text']
            
            if filename not in hits_by_professor:
                hits_by_professor[filename] = []
            hits_by_professor[filename].append(text_chunk)

    # 4. Format into a string for the Prompt
    context_str = ""
    for filename, chunks in hits_by_professor.items():
        context_str += f"### CANDIDATE: {filename}\n"
        context_str += "RELEVANT EXCERPTS:\n"
        for i, chunk in enumerate(chunks, 1):
            context_str += f"...{chunk}...\n"
        context_str += "\n"
        
    return context_str, list(hits_by_professor.keys())

def main():
    # 1. SETUP
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in .env")
        return

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_output = project_root / "data" / "output"
    
    # Define Input Files
    # In a real app, this would be dynamic. For prototype, we point to one.
    award_file = data_output / "5.02_Research Excellence.txt" 
    prompt_file = script_dir / "prompts" / "award_to_cvs_prompt.md"

    # 2. LOAD RESOURCES
    try:
        index, metadata = load_resources(data_output)
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(e)
        return

    # 3. READ INPUTS
    print(f"Reading award: {award_file.name}")
    with open(award_file, "r", encoding="utf-8") as f:
        award_text = f.read()

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()

    # 4. RETRIEVE
    context_string, matched_files = get_relevant_context(award_text, index, metadata, model, TOP_K_CHUNKS)
    
    print(f"Found relevant matches in: {matched_files}")

    # 5. CONSTRUCT PROMPT
    final_prompt = prompt_template.replace("{AWARD_TEXT}", award_text).replace("{CV_TEXT}", context_string)

    # 6. LLM CALL
    print("Calling LLM for evaluation...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": "qwen/qwen3-coder:free", # Or your preferred model
            "messages": [{"role": "user", "content": final_prompt}]
        }
    )

    # 7. OUTPUT
    data = response.json()
    if "choices" in data:
        result_text = data["choices"][0]["message"]["content"]
        print("\n=== MATCHING RESULTS ===\n")
        print(result_text)
    else:
        print("\nError from API:", data)

if __name__ == "__main__":
    main()