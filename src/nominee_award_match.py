"""
Match a nominee's resume text to extracted award descriptions using the same embedding model as CV ingest.
Awards live on disk (data/output); they are not stored in Pinecone.
"""
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from config import OUTPUT_DIR


def list_award_text_files() -> list[Path]:
    if not OUTPUT_DIR.exists():
        return []
    return sorted(OUTPUT_DIR.glob("*.txt"))


def load_award_documents() -> list[tuple[str, str]]:
    """Return list of (filename, full_text)."""
    docs = []
    for path in list_award_text_files():
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if text:
            docs.append((path.name, text))
    return docs


def match_resume_to_awards(
    resume_text: str,
    model: SentenceTransformer,
    top_n: int = 10,
) -> list[dict]:
    """
    Embed resume and each award file; rank by cosine similarity.

    Returns:
        List of dicts: filename, score (0-1), preview (first ~400 chars of award text)
    """
    resume_text = (resume_text or "").strip()
    if not resume_text:
        return []

    docs = load_award_documents()
    if not docs:
        return []

    filenames = [d[0] for d in docs]
    bodies = [d[1] for d in docs]

    resume_emb = model.encode([resume_text], show_progress_bar=False)
    award_embs = model.encode(bodies, show_progress_bar=False)
    sims = cosine_similarity(resume_emb, award_embs)[0]

    ranked_idx = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_n]

    out = []
    for i in ranked_idx:
        body = bodies[i]
        preview = body.replace("\n", " ")[:400]
        if len(body) > 400:
            preview += "…"
        out.append(
            {
                "filename": filenames[i],
                "score": float(sims[i]),
                "preview": preview,
            }
        )
    return out
