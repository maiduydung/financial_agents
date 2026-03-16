"""FastAPI server for the Financial Analyst Agent."""

import logging
from fastapi import FastAPI
from pydantic import BaseModel
from app.agent import run_agent
from app.browser_agent import run_browser_agent

app = FastAPI(title="Financial Analyst Agent", version="0.1.0")
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


class EnrichRequest(BaseModel):
    task: str


class EnrichResponse(BaseModel):
    summary: str


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Ask the Financial Analyst Agent a question."""
    logger.info("📩 Received query: %s", request.question)
    answer = await run_agent(request.question)
    logger.info("✅ Agent response ready (%d chars)", len(answer))
    return QueryResponse(answer=answer)


@app.post("/enrich", response_model=EnrichResponse)
async def enrich(request: EnrichRequest):
    """Use the browser agent to research and enrich the knowledge base."""
    logger.info("🌐 Received enrich task: %s", request.task)
    summary = await run_browser_agent(request.task)
    logger.info("✅ Enrichment complete (%d chars)", len(summary))
    return EnrichResponse(summary=summary)


@app.get("/health")
async def health():
    return {"status": "ok"}
