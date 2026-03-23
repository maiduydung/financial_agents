# Company Analyst Agent

LangGraph-based agent that answers questions about companies using RAG, live API data, and web search (Tavily). Features a Streamlit chat UI with real-time agent activity logs.

## Architecture

```mermaid
flowchart TD
    subgraph ui["Streamlit Chat UI"]
        Chat["Chat Interface"]
        Logs["Live Agent Logs (SSE)"]
    end

    subgraph api["FastAPI Server"]
        A1["POST /query"]
        A2["POST /query/stream (SSE)"]
        A3["POST /enrich"]
    end

    subgraph agent["LangGraph Analyst Agent"]
        direction TB
        SP[System Prompt] --> LLM["GPT-4o-mini"]
        LLM -->|tool calls?| Decision{Has tool calls?}
        Decision -->|Yes| Tools["ToolNode"]
        Decision -->|No| Answer["Final Answer"]
        Tools --> LLM
    end

    subgraph tools["Agent Tools"]
        T1["retrieve_docs\nVector DB search"]
        T2["fetch_company_metrics\nLive financial ratios"]
        T3["run_basic_financial_checks\nRevenue, debt, margins"]
        T4["generate_analysis\nSynthesize findings"]
        T5["web_search\nTavily quick search"]
        T6["web_extract\nRead full URL content"]
        T7["web_research\nDeep multi-source research"]
    end

    subgraph ingestor["Azure Functions Ingestor"]
        I1["POST /api/ingest/{symbol}\nFMP data pipeline"]
        I2["POST /api/ingestLLMData\nAgent web data pipeline"]
        Chunk["Chunk (500 chars)"]
        Embed["OpenAI Embeddings"]
    end

    subgraph external["External Services"]
        Chroma["Chroma Cloud"]
        FMP["FMP API"]
        OAI["OpenAI API"]
        Tavily["Tavily API"]
    end

    Chat --> A2
    A2 -->|logs + answer| Logs
    A1 --> agent
    A2 --> agent

    Tools --> T1 & T2 & T3 & T4 & T5 & T6 & T7

    T1 --> Chroma
    T2 & T3 --> FMP
    T5 & T6 & T7 --> Tavily
    T5 & T6 & T7 -->|store results| I2

    I1 --> Chunk --> Embed --> Chroma
    I2 --> Chunk

    LLM --> OAI

    style ui fill:#fce4ec,stroke:#e91e63,color:#333
    style api fill:#e0f2f1,stroke:#009688,color:#333
    style agent fill:#e8eaf6,stroke:#3f51b5,color:#333
    style tools fill:#f3e5f5,stroke:#9c27b0,color:#333
    style ingestor fill:#e3f2fd,stroke:#1565c0,color:#333
    style external fill:#f5f5f5,stroke:#757575,color:#333
```

### Agent Workflow

```mermaid
sequenceDiagram
    participant User
    participant Streamlit
    participant FastAPI
    participant Agent as Analyst Agent
    participant Tavily
    participant Ingestor as Azure Functions Ingestor
    participant Chroma as Chroma Cloud
    participant FMP as FMP API

    User->>Streamlit: "Tell me about Apple"
    Streamlit->>FastAPI: POST /query/stream (+ chat history)
    FastAPI->>Agent: run_agent(question, history)
    FastAPI-->>Streamlit: SSE: log events (real-time)

    Agent->>Chroma: retrieve_docs("Apple")
    Chroma-->>Agent: Relevant documents

    Agent->>FMP: fetch_company_metrics("AAPL")
    FMP-->>Agent: Financial ratios

    Agent->>FMP: run_basic_financial_checks("AAPL")
    FMP-->>Agent: Health flags

    opt Needs more context
        Agent->>Tavily: web_search("AAPL latest news")
        Tavily-->>Agent: Search results
        Agent->>Ingestor: POST /api/ingestLLMData
        Ingestor->>Chroma: Chunk + embed + store
    end

    opt Has a specific URL to read
        Agent->>Tavily: web_extract("https://...")
        Tavily-->>Agent: Full page content
        Agent->>Ingestor: POST /api/ingestLLMData
        Ingestor->>Chroma: Chunk + embed + store
    end

    Agent-->>FastAPI: Final analysis
    FastAPI-->>Streamlit: SSE: answer event
    Streamlit-->>User: Rendered answer + collapsed logs
```

### Data Enrichment Flow

```mermaid
flowchart LR
    A["Tavily API"] -->|search / extract / research| B["Raw Content"]
    B -->|POST /api/ingestLLMData| C["Azure Functions Ingestor"]
    C --> D["Chunk (500 chars)"]
    D --> E["OpenAI Embeddings"]
    E --> F["Chroma Cloud"]
    F -->|future queries| G["retrieve_docs"]
    G -->|used by| H["Analyst Agent"]
```

## Setup

1. Copy `.env.example` to `.env` and fill in your keys:
   ```
   OPENAI_API_KEY=...
   CHROMA_API_KEY=...
   CHROMA_TENANT=...
   CHROMA_DATABASE=...
   FMP_API_KEY=...
   TAVILY_API_KEY=...
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the Azure Functions ingestor (see `financial_data` repo):
   ```bash
   cd ../financial_data && func start
   ```

## Run

**Start the API server:**
```bash
uvicorn app.main:app --reload --port 8000
```

**Start the Streamlit UI (separate terminal):**
```bash
streamlit run ui/streamlit_app.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/query` | POST | Ask the analyst agent a question |
| `/query/stream` | POST | SSE stream — logs + final answer |
| `/enrich` | POST | Standalone web enrichment |
| `/health` | GET | Health check |

## Agent Tools

| Tool | Description | Data Source |
|------|-------------|-------------|
| `retrieve_docs` | Search the vector database | Chroma Cloud |
| `fetch_company_metrics` | Live financial ratios (public companies) | FMP API |
| `run_basic_financial_checks` | Revenue, debt, margin checks | FMP API |
| `generate_analysis` | Synthesize findings into analysis | LLM |
| `web_search` | Quick web search | Tavily |
| `web_extract` | Read full content of a URL | Tavily |
| `web_research` | Deep multi-source research | Tavily |
