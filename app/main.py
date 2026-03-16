"""FastAPI server for the Financial Analyst Agent."""

import logging
from fastapi import FastAPI
from pydantic import BaseModel
from app.agent import run_agent

app = FastAPI(title="Financial Analyst Agent", version="0.1.0")
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Ask the Financial Analyst Agent a question."""
    logger.info("📩 Received query: %s", request.question)
    answer = await run_agent(request.question)
    logger.info("✅ Agent response ready (%d chars)", len(answer))
    return QueryResponse(answer=answer)


@app.get("/health")
async def health():
    return {"status": "ok"}
