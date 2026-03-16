# Financial Analyst Agent

LangGraph-based agent that answers financial questions about companies using RAG (Retrieval-Augmented Generation).

## Architecture

```mermaid
flowchart TD
    subgraph ui["🖥️ Streamlit UI"]
        U[User Question]
    end

    subgraph api["⚡ FastAPI Server"]
        A["POST /query"]
    end

    subgraph agent["🤖 LangGraph Agent"]
        direction TB
        S[System Prompt] --> LLM["GPT-4o-mini"]
        LLM -->|tool_calls?| Decision{Has tool calls?}
        Decision -->|Yes| Tools
        Decision -->|No| Answer["💬 Final Answer"]
        Tools --> LLM
    end

    subgraph tools["🔧 Agent Tools"]
        T1["📚 retrieve_docs\nChroma Cloud vector search"]
        T2["📊 fetch_company_metrics\nLive FMP API ratios"]
        T3["🏥 run_basic_financial_checks\nRevenue trend · Debt ratio · Margins"]
        T4["🧪 generate_analysis\nLLM synthesis signal"]
    end

    subgraph external["🌐 External Services"]
        Chroma["🧠 Chroma Cloud\nfinancial_docs collection"]
        FMP["📡 FMP Stable API\nLive financial data"]
        OAI["OpenAI\nEmbeddings + LLM"]
    end

    U --> A --> agent
    T1 --> Chroma
    T1 --> OAI
    T2 --> FMP
    T3 --> FMP
    LLM --> OAI
    agent --> Answer --> A --> U

    style ui fill:#ff4b4b,color:#fff
    style api fill:#009688,color:#fff
    style agent fill:#1a1a2e,color:#fff
    style external fill:#374151,color:#fff
```

### Agent Workflow

```mermaid
sequenceDiagram
    participant User
    participant FastAPI
    participant Agent as LangGraph Agent
    participant Tools
    participant Chroma as Chroma Cloud
    participant FMP as FMP API

    User->>FastAPI: "Financial health summary for Apple"
    FastAPI->>Agent: run_agent(question)

    Agent->>Tools: retrieve_docs(query="Apple financial health", company="AAPL")
    Tools->>Chroma: Vector similarity search
    Chroma-->>Tools: Matching documents + metadata
    Tools-->>Agent: Formatted context

    Agent->>Tools: fetch_company_metrics(company="AAPL")
    Tools->>FMP: GET /stable/ratios?symbol=AAPL
    FMP-->>Tools: Current ratios, margins, P/E
    Tools-->>Agent: Formatted metrics

    Agent->>Tools: run_basic_financial_checks(company="AAPL")
    Tools->>FMP: GET /stable/income-statement + /ratios
    FMP-->>Tools: 3-year data
    Tools-->>Agent: ✓/⚠ flags (revenue, debt, margins)

    Agent->>Agent: Synthesize all findings
    Agent-->>FastAPI: Final analysis
    FastAPI-->>User: Structured answer with citations
```

## Setup

1. Copy `.env.example` to `.env` and fill in your keys
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
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

## Example Questions

- "Give me a quick financial health summary for Apple."
- "Why might Nvidia's margins be changing?"
- "Are there any financial risk signals for Microsoft?"
