"""FastAPI server for the Financial Analyst Agent."""

import asyncio
import json
import logging
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agent import run_agent
from app.browser_agent import run_browser_enrich

app = FastAPI(title="Financial Analyst Agent", version="0.1.0")
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []


class QueryResponse(BaseModel):
    answer: str


class EnrichRequest(BaseModel):
    task: str


class EnrichResponse(BaseModel):
    summary: str


class _LogCapture(logging.Handler):
    """Captures log records and pushes them to an asyncio queue."""

    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord):
        try:
            self.queue.put_nowait(record.getMessage())
        except asyncio.QueueFull:
            pass


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Ask the Financial Analyst Agent a question."""
    logger.info("📩 Received query: %s", request.question)
    history = [(msg.role, msg.content) for msg in request.history]
    answer = await run_agent(request.question, history=history)
    logger.info("✅ Agent response ready (%d chars)", len(answer))
    return QueryResponse(answer=answer)


@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """SSE endpoint: streams log lines while the agent works, then sends the final answer."""
    log_queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    handler = _LogCapture(log_queue)
    handler.setLevel(logging.INFO)

    # Attach handler to root logger so we capture all app.* logs
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    history = [(msg.role, msg.content) for msg in request.history]

    # Run the agent in a background task
    agent_task = asyncio.create_task(run_agent(request.question, history=history))

    async def event_generator():
        try:
            while not agent_task.done():
                try:
                    msg = await asyncio.wait_for(log_queue.get(), timeout=0.3)
                    yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                except asyncio.TimeoutError:
                    continue

            # Drain remaining logs
            while not log_queue.empty():
                msg = log_queue.get_nowait()
                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"

            answer = await agent_task
            yield f"data: {json.dumps({'type': 'answer', 'message': answer})}\n\n"
        finally:
            root_logger.removeHandler(handler)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/enrich", response_model=EnrichResponse)
async def enrich(request: EnrichRequest):
    """Use the browser agent to research and enrich the knowledge base."""
    logger.info("🌐 Received enrich task: %s", request.task)
    # Extract company from task or default to general
    company = "GENERAL"
    for ticker in ["AAPL", "MSFT", "NVDA", "GOOG", "AMZN", "META", "TSLA"]:
        if ticker.lower() in request.task.lower():
            company = ticker
            break
    summary = await run_browser_enrich(request.task, company)
    logger.info("✅ Enrichment complete (%d chars)", len(summary))
    return EnrichResponse(summary=summary)


@app.get("/health")
async def health():
    return {"status": "ok"}
