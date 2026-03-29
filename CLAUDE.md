# CLAUDE.md — LLM Context for Financial Analyst Agent

## What is this project?

A LangGraph-based financial analyst agent that answers questions about companies by combining RAG (vector search over ingested financial documents), live API data from Financial Modeling Prep, and Tavily web search. It exposes a FastAPI backend with SSE streaming and ships with a Streamlit chat UI that shows real-time agent activity logs.

## Tech stack

- **Agent framework:** LangGraph + LangChain
- **LLM:** OpenAI GPT (configurable via `OPENAI_MODEL`)
- **Vector DB:** Chroma Cloud
- **Embeddings:** OpenAI `text-embedding-3-small`
- **Financial data:** Financial Modeling Prep (FMP) API
- **Web search:** Tavily (search, extract, deep research)
- **API server:** FastAPI with SSE streaming
- **UI:** Streamlit chat interface
- **Browser automation:** browser-use + Playwright (for the enrichment endpoint)
- **HTTP client:** httpx (no requests/axios)
- **Language:** Python 3.11+, type hints throughout

## Key files

| File | Purpose |
|------|---------|
| `app/agent.py` | LangGraph state machine — builds the agent/tools/continue graph, runs queries |
| `app/tools.py` | All 7 agent tools: retrieve_docs, fetch_company_metrics, run_basic_financial_checks, generate_analysis, web_search, web_extract, web_research |
| `app/retriever.py` | Chroma Cloud vector search — embeds query, retrieves top-k docs |
| `app/enrichment.py` | Chunking + embedding pipeline — stores text in Chroma Cloud |
| `app/browser_agent.py` | Headless browser agent for on-demand web enrichment |
| `app/main.py` | FastAPI server — /query, /query/stream (SSE), /enrich, /health |
| `config/settings.py` | All env vars loaded via python-dotenv |
| `ui/streamlit_app.py` | Streamlit chat UI with SSE log streaming |
| `sample.ipynb` | Quick notebook for testing Tavily extraction |

## Architecture overview

```
User -> Streamlit UI -> FastAPI (/query/stream SSE)
                            |
                      LangGraph Agent (agent node <-> tool node loop)
                            |
              +-------------+-------------+
              |             |             |
         Chroma Cloud   FMP API     Tavily API
         (RAG search)   (metrics)   (web search)
              |
     Azure Functions Ingestor (optional, stores web results)
```

The agent is a simple two-node LangGraph state machine:
1. **agent** node — calls the LLM with system prompt + message history
2. **tools** node — executes whichever tools the LLM requested
3. Conditional edge: if the LLM returned tool calls, route to tools; otherwise END

Web search results are automatically forwarded to an Azure Functions ingestor service that chunks, embeds, and stores them in Chroma for future retrieval.

## How to run

```bash
# 1. Set up environment
cp .env.example .env
# Fill in your API keys

# 2. Install dependencies
pip install -r requirements.txt
playwright install  # for browser agent

# 3. Start the API server
uvicorn app.main:app --reload --port 8000

# 4. Start the Streamlit UI (separate terminal)
streamlit run ui/streamlit_app.py
```

Optionally start the Azure Functions ingestor (`financial_data` repo) on port 7071 for automatic web result ingestion.

## Important patterns

- **All secrets come from env vars** — loaded in `config/settings.py` via `python-dotenv`. Never hardcode keys.
- **Agent singleton** — `agent.py` compiles the graph once at module level (`agent = build_graph()`).
- **SSE streaming** — `/query/stream` captures Python logger output via a custom `_LogCapture` handler, streams log lines as SSE events, then sends the final answer.
- **Tavily results are auto-ingested** — every `web_search`, `web_extract`, and `web_research` call forwards extracted text to the ingestor, building the knowledge base over time.
- **Graceful degradation** — if the ingestor service is unavailable, tools still return results to the agent; they just skip storage.
- **Tool definitions use `@tool` decorator** from `langchain_core.tools` with full docstrings that serve as the LLM's tool descriptions.

## Companion repo

- **financial_data** — Azure Function App that handles the FMP data ingestion pipeline (pull from API -> Blob Storage -> chunk -> embed -> Chroma Cloud).
