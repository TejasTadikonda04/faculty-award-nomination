"""
HTTP API for the faculty award nomination UI (FastAPI).
"""
import json
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from config import CV_DIR, EMBEDDING_MODEL_NAME, OUTPUT_DIR, validate_api_config
from ingest_cv import extract_text_from_pdf
from nominee_award_match import load_award_documents, match_resume_to_awards
from rag_matching import load_pinecone_index, match_award_text_to_faculty

# Heavier retrieval so multiple faculty appear in context for top-10 ranking
NOMINATOR_TOP_K = 120
_model: SentenceTransformer | None = None
_index = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def get_index():
    global _index
    if _index is None:
        _index = load_pinecone_index()
    return _index


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        validate_api_config()
    except ValueError as e:
        print(f"API config warning: {e}")
    yield


app = FastAPI(
    title="Faculty Award Nomination API",
    description="RAG + LLM matching for Texas A&M research awards",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def safe_award_path(filename: str) -> Path:
    name = Path(filename).name
    path = OUTPUT_DIR / name
    if not path.is_file() or path.suffix.lower() != ".txt":
        raise HTTPException(status_code=404, detail="Award not found")
    try:
        path.resolve().relative_to(OUTPUT_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    return path


def parse_nominator_json(raw: str) -> dict | None:
    text = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        text = m.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


class NomineeMatchRequest(BaseModel):
    resume_text: str = Field(..., min_length=20)
    top_n: int = Field(10, ge=1, le=30)


class NominatorRankRequest(BaseModel):
    criteria_text: str = Field(..., min_length=20)
    department: str | None = Field(
        None,
        description="Optional substring to filter faculty names (filename stems in Pinecone)",
    )


@app.get("/api/health")
def health():
    try:
        validate_api_config()
        config_ok = True
        config_error = None
    except ValueError as e:
        config_ok = False
        config_error = str(e)
    awards_dir_exists = OUTPUT_DIR.exists()
    award_count = len(list(OUTPUT_DIR.glob("*.txt"))) if awards_dir_exists else 0
    return {
        "status": "ok",
        "config_ok": config_ok,
        "config_error": config_error,
        "awards_extracted_count": award_count,
        "pinecone_note": "CV chunks live in Pinecone; run ingest-cvs after adding PDFs to data/cv",
    }


@app.get("/api/awards")
def list_awards(q: str | None = Query(None, description="Filter by filename or content")):
    docs = load_award_documents()
    items = []
    for filename, text in docs:
        preview = text.replace("\n", " ")[:280]
        if len(text) > 280:
            preview += "…"
        title = filename.replace(".txt", "").replace("_", " ")
        items.append({"filename": filename, "title": title, "preview": preview})
    if q and q.strip():
        needle = q.strip().lower()
        items = [
            i
            for i in items
            if needle in i["filename"].lower()
            or needle in i["preview"].lower()
            or needle in i["title"].lower()
        ]
    return {"awards": items}


@app.get("/api/awards/{filename:path}")
def get_award(filename: str):
    path = safe_award_path(filename)
    return {"filename": path.name, "text": path.read_text(encoding="utf-8")}


@app.get("/api/cvs")
def list_cvs():
    if not CV_DIR.exists():
        return {"cvs": []}
    files = sorted(CV_DIR.glob("*.pdf"))
    return {"cvs": [f.name for f in files]}


@app.get("/api/cvs/{filename:path}")
def get_cv(filename: str):
    name = Path(filename).name
    path = CV_DIR / name
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="CV not found")
    try:
        path.resolve().relative_to(CV_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    text = extract_text_from_pdf(path)
    if not text:
        raise HTTPException(status_code=422, detail="Could not extract text from PDF")
    return {"filename": name, "text": text}


@app.post("/api/nominee/match-resume")
def nominee_match_resume(body: NomineeMatchRequest):
    model = get_model()
    matches = match_resume_to_awards(body.resume_text, model, top_n=body.top_n)
    if not matches and not load_award_documents():
        raise HTTPException(
            status_code=503,
            detail="No award text files in data/output. Run extract-awards with Excel in data/awards.",
        )
    return {"matches": matches}


@app.post("/api/nominator/rank-faculty")
def nominator_rank(body: NominatorRankRequest):
    try:
        validate_api_config()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    model = get_model()
    index = get_index()
    raw = match_award_text_to_faculty(
        body.criteria_text.strip(),
        index,
        model,
        top_k=NOMINATOR_TOP_K,
        department_filter=body.department,
    )
    parsed = parse_nominator_json(raw)
    return {"raw_response": raw, "rankings": parsed.get("rankings") if parsed else None}


def main():
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
