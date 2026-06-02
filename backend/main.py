"""Gemini Shadow Courtroom — FastAPI backend.

Routes
------
POST /log          Receive a {prompt, response, timestamp} payload, fan out to
                   judges, write the courtroom transcript to Google Docs, and
                   return the verdict.
GET  /health       Railway / uptime health check.
GET  /exchanges    Return the current in-memory exchange buffer (debug).

All integrations (Google Docs, OpenRouter judges, Sheets cron) degrade
gracefully to no-ops when their API keys are absent — the server always
starts and the /health endpoint always returns 200.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Lazy imports for optional integrations
# ---------------------------------------------------------------------------
from backend import google_docs, judges, scheduler  # noqa: E402

# Shared in-memory exchange buffer — drained every N hours by the scheduler.
_exchange_buffer: list = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print("\n=== Gemini Shadow Courtroom backend starting ===")
    google_docs.init()
    judges.init()
    scheduler.init(_exchange_buffer)
    print("=================================================\n")
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Gemini Shadow Courtroom",
    description="Logs Gemini exchanges, fans out to three AI judges, "
                "stores transcripts in Google Docs, summaries in Google Sheets.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class LogRequest(BaseModel):
    prompt: str
    response: str
    timestamp: Optional[str] = None


class JudgeOpinion(BaseModel):
    judge: str
    model: str
    text: str


class LogResponse(BaseModel):
    status: str
    timestamp: str
    doc_written: bool
    judge_opinions: list[JudgeOpinion]
    doc_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "gemini-shadow-courtroom"}


@app.get("/exchanges")
async def list_exchanges():
    """Return current buffered exchanges (for debugging)."""
    return {"count": len(_exchange_buffer), "exchanges": _exchange_buffer[-20:]}


@app.post("/log", response_model=LogResponse)
async def log_exchange(req: LogRequest):
    """Core endpoint: receive an exchange, judge it, and store it."""
    ts = req.timestamp or datetime.now(timezone.utc).isoformat()

    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="prompt must not be empty")
    if not req.response.strip():
        raise HTTPException(status_code=400, detail="response must not be empty")

    # Fan out to judges in parallel (no-op if OpenRouter key absent).
    opinions = await judges.get_opinions(req.prompt, req.response)

    # Build the courtroom block and write to Google Docs.
    block = google_docs.format_courtroom_block(
        prompt=req.prompt,
        response=req.response,
        timestamp=ts,
        judge_opinions=opinions or None,
    )
    doc_written = google_docs.append_to_doc(block)

    # Buffer the exchange for the periodic Sheets summary.
    _exchange_buffer.append({
        "timestamp": ts,
        "prompt": req.prompt,
        "response": req.response,
    })

    gdoc_id = os.getenv("GDOC_ID")
    doc_url = (
        f"https://docs.google.com/document/d/{gdoc_id}/edit"
        if gdoc_id and doc_written
        else None
    )

    return LogResponse(
        status="ok",
        timestamp=ts,
        doc_written=doc_written,
        judge_opinions=[JudgeOpinion(**o) for o in opinions],
        doc_url=doc_url,
    )
