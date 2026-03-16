# Financial Analyst Agent

LangGraph-based agent that answers financial questions about companies using RAG, live API data, and on-demand web browsing.

## Architecture

```mermaid
flowchart TD
    subgraph ui["🖥️ Streamlit UI"]
        U1["🤖 Ask Agent tab"]
        U2["🌐 Web Enrichment tab"]
    end

    subgraph api["⚡ FastAPI Server"]
        A1["POST /query"]
        A2["POST /enrich"]
    end

    subgraph analyst["🤖 Financial Analyst Agent (LangGraph)"]
        direction TB
        S1[System Prompt] --> LLM1["GPT-4o-mini"]
        LLM1 -->|tool_calls?| D1{Has tool calls?}
        D1 -->|Yes| T1[Tools]
        D1 -->|No| Ans1["💬 Final Answer"]
        T1 --> LLM1
    end

    subgraph browser["🌐 Browser Agent (LangGraph)"]
        direction TB
        S2[System Prompt] --> LLM2["GPT-4o-mini"]
        LLM2 -->|tool_calls?| D2{Has tool calls?}
        D2 -->|Yes| T2[Tools]
        D2 -->|No| Ans2["💬 Summary"]
        T2 --> LLM2
    end

    subgraph analyst_tools["🔧 Analyst Tools"]
        AT1["📚 retrieve_docs"]
        AT2["📊 fetch_company_metrics"]
        AT3["🏥 run_basic_financial_checks"]
        AT4["🧪 generate_analysis"]
        AT5["🌐 web_enrich → triggers Browser Agent"]
    end

    subgraph browser_tools["🔧 Browser Tools"]
        BT1["🌐 browse_and_extract\n(Playwright + browser-use)"]
        BT2["💾 store_enrichment\n→ chunk → embed → Chroma"]
    end

    subgraph external["🌐 External Services"]
        Chroma["🧠 Chroma Cloud"]
        FMP["📡 FMP API"]
        OAI["OpenAI"]
        Web["🌍 The Internet\n(via headless Chrome)"]
    end

    U1 --> A1 --> analyst
    U2 --> A2 --> browser
    AT5 -.->|on demand| browser

    AT1 --> Chroma
    AT2 & AT3 --> FMP
    BT1 --> Web
    BT2 --> Chroma
    LLM1 & LLM2 --> OAI

    style ui fill:#ff4b4b,color:#fff
    style api fill:#009688,color:#fff
    style analyst fill:#1a1a2e,color:#fff
    style browser fill:#1a1a2e,color:#fff
    style external fill:#374151,color:#fff
```

### Agent Workflow

```mermaid
sequenceDiagram
    participant User
    participant FastAPI
    participant Analyst as Analyst Agent
    participant Browser as Browser Agent
    participant Chrome as Headless Chrome
    participant Chroma as Chroma Cloud
    participant FMP as FMP API

    User->>FastAPI: "Financial health summary for Apple"
    FastAPI->>Analyst: run_agent(question)

    Analyst->>Analyst: retrieve_docs → Chroma
    Analyst->>Analyst: fetch_company_metrics → FMP
    Analyst->>Analyst: run_basic_financial_checks → FMP

    alt Needs more context
        Analyst->>Browser: web_enrich("Find recent AAPL news", "AAPL")
        Browser->>Chrome: Navigate, search, extract
        Chrome-->>Browser: Extracted text
        Browser->>Chroma: store_enrichment (chunk → embed → store)
        Browser-->>Analyst: Enrichment summary
    end

    Analyst-->>FastAPI: Final analysis
    FastAPI-->>User: Structured answer with citations
```

### Data Enrichment Flow

```mermaid
flowchart LR
    A["🌐 Browser Agent"] -->|extracts text| B["📄 Raw Content"]
    B --> C["✂️ Chunk (500 chars)"]
    C --> D["🧠 OpenAI Embeddings"]
    D --> E["💾 Chroma Cloud"]
    E -->|available to| F["📚 retrieve_docs"]
    F -->|used by| G["🤖 Analyst Agent"]
```

## Setup

1. Copy `.env.example` to `.env` and fill in your keys
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Make sure you've run the ingestion pipeline (see `financial_data` repo) first

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
| `/query` | POST | Ask the analyst agent a financial question |
| `/enrich` | POST | Use browser agent to research and enrich the knowledge base |
| `/health` | GET | Health check |

## Example Questions

- "Give me a quick financial health summary for Apple."
- "Why might Nvidia's margins be changing?"
- "Are there any financial risk signals for Microsoft?"
- "Find the latest earnings call highlights for NVDA and analyze them."
