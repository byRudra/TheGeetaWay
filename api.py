"""
TheGeetaWay API - Your Path to Ancient Wisdom
A RESTful API for Bhagavad Gita verse search and AI-powered spiritual guidance
"""

from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, HTTPException, Query, Path, BackgroundTasks, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import sys
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# ========================================================================
# PATH SETUP
# ========================================================================

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ========================================================================
# IMPORTS
# ========================================================================

try:
    from embeddings.query_faiss import search_gita, load_resources, enhance_query_contextual
    from reasoning.llm_reasoning import reason_over_verses
except ImportError:
    from query_faiss import search_gita, load_resources, enhance_query_contextual
    from llm_reasoning import reason_over_verses

# ========================================================================
# CONFIG
# ========================================================================
API_KEY = os.getenv("API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


# ========================================================================
# AUTH
# ========================================================================

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return api_key

# ========================================================================
# MODELS
# ========================================================================

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    top_k: int = Field(5, ge=1, le=10)
    include_guidance: bool = True
    filter_practical: bool = True

    @validator("question")
    def clean_question(cls, v):
        return v.strip()


class VerseResponse(BaseModel):
    id: str
    chapter: int
    verse: int
    sanskrit: str
    english: str
    score: float
    themes: List[str] = []
    is_practical: bool = False
    audio_url: str
    context_warning: Optional[str] = None
    relevance_adjusted: Optional[float] = None


class GuidanceResponse(BaseModel):
    guidance_text: str
    selected_verse: Dict[str, Any]
    generated_at: datetime
    model_used: str = "groq-llama-3.3-70b"


class SearchResponse(BaseModel):
    query: str
    enhanced_query: str
    verses: List[VerseResponse]
    guidance: Optional[GuidanceResponse]
    total_verses: int
    processing_time_ms: float
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    app_name: str
    faiss_loaded: bool
    model_loaded: bool
    total_verses: int
    timestamp: datetime


class StatsResponse(BaseModel):
    total_verses: int
    total_chapters: int
    queries_processed: int
    uptime_seconds: float

# ========================================================================
# APP
# ========================================================================

app = FastAPI(
    title="🪔 TheGeetaWay API",
    description="Your Path to Ancient Wisdom",
    version="1.0.0"
)

# ========================================================================
# CORS
# ========================================================================

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# GLOBAL STATE
# ========================================================================

app.state.start_time = datetime.now()
app.state.query_count = 0
app.state.resources_loaded = False

# ========================================================================
# AUDIO URL FIX (IMPORTANT)
# ========================================================================

def get_audio_url(chapter: int, verse: int) -> str:
    """
    IIT Kanpur audio server requires NON zero-padded values
    ✅ CHAP5/5-4.MP3
    ❌ CHAP05/05-04.MP3
    """
    chapter = int(chapter)
    verse = int(verse)
    return (
        "https://gitasupersite.iitk.ac.in/sites/default/files/audio/"
        f"CHAP{chapter}/{chapter}-{verse}.MP3"
    )

# ========================================================================
# HELPERS
# ========================================================================

def format_verse_response(verse: Dict[str, Any]) -> VerseResponse:
    return VerseResponse(
        id=f"{verse['chapter']}.{verse['verse']}",
        chapter=verse["chapter"],
        verse=verse["verse"],
        sanskrit=verse["sanskrit"],
        english=verse["english"],
        score=verse["score"],
        themes=verse.get("themes", []),
        is_practical=verse.get("is_practical", False),
        audio_url=get_audio_url(verse["chapter"], verse["verse"]),
        context_warning=verse.get("context_warning"),
        relevance_adjusted=verse.get("relevance_adjusted", verse["score"]),
    )


@lru_cache(maxsize=1)
def load_app_resources():
    model, index, metadata = load_resources()
    app.state.resources_loaded = True
    return model, index, metadata


def increment_query_count():
    app.state.query_count += 1

# ========================================================================
# STARTUP
# ========================================================================

@app.on_event("startup")
async def startup_event():
    load_app_resources()

# ========================================================================
# HEALTH
# ========================================================================

@app.get("/health", response_model=HealthResponse)
async def health():
    model, index, metadata = load_app_resources()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        app_name="TheGeetaWay",
        faiss_loaded=True,
        model_loaded=True,
        total_verses=len(metadata),
        timestamp=datetime.now(),
    )

# ========================================================================
# SEARCH
# ========================================================================

@app.post(
    "/api/v1/search",
    response_model=SearchResponse,
    dependencies=[Security(verify_api_key)]
)
async def search(request: QueryRequest, background_tasks: BackgroundTasks):
    import time
    start = time.time()

    background_tasks.add_task(increment_query_count)

    results = search_gita(
        request.question,
        top_k=request.top_k,
        filter_practical=request.filter_practical,
    )

    if not results:
        raise HTTPException(status_code=404, detail="No verses found")

    verses = [format_verse_response(v) for v in results]

    guidance = None
    if request.include_guidance:
        try:
            text = reason_over_verses(request.question, results)
        except Exception:
            logger.exception("Guidance generation failed")
            text = None

        # A guidance failure must never take down the whole response - the
        # retrieved verses are still useful on their own.
        if not isinstance(text, str) or not text.strip():
            text = (
                "\U0001f30c Guidance is temporarily unavailable, but the verses "
                "above still speak to your question. Please try again shortly."
            )

        guidance = GuidanceResponse(
            guidance_text=text,
            selected_verse={
                "chapter": results[0]["chapter"],
                "verse": results[0]["verse"],
                "english": results[0]["english"],
            },
            generated_at=datetime.now(),
        )

    enhanced = enhance_query_contextual(request.question)

    return SearchResponse(
        query=request.question,
        enhanced_query=enhanced,
        verses=verses,
        guidance=guidance,
        total_verses=len(verses),
        processing_time_ms=round((time.time() - start) * 1000, 2),
        timestamp=datetime.now(),
    )

# ========================================================================
# MAIN
# ========================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
