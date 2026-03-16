You are a senior AI systems engineer.

Your task is to generate a **complete minimal working project** that demonstrates a production-style GenAI architecture with the following components:

* Data ingestion pipeline
* Azure-based storage
* Vector indexing
* Retrieval-augmented generation
* LangGraph agent workflow
* Simple demo UI

The project should be clean, minimal, and realistic for a technical interview demo.

Do NOT overengineer the system. Keep it simple and reliable.

---

PROJECT GOAL

Build a **Financial Analyst Agent** prototype.

The system should ingest financial data from a public API, process it, store embeddings in a vector database, and allow a LangGraph agent to answer questions about companies using retrieved knowledge and simple analysis tools.

---

DATA SOURCE

Use the **Financial Modeling Prep API**.

Fetch data for 2–3 companies (for example: AAPL, MSFT, NVDA).

Pull the following endpoints:

1. Company profile
2. Income statement
3. Financial ratios
4. Company news

Convert this into structured JSON documents.

---

SYSTEM ARCHITECTURE

Data ingestion pipeline:

API Puller
↓
Azure Blob Storage (raw zone)
↓
Processing script
↓
Clean + normalize data
↓
Chunk documents
↓
Generate embeddings
↓
Store in Chroma Cloud vector database

Application layer:

FastAPI server
↓
LangGraph agent
↓
Tools:

* retrieve_docs()
* fetch_company_metrics()
* run_basic_financial_checks()
* generate_analysis()

User interface:

Simple Streamlit or CLI interface where the user can ask questions about companies.

---

INGESTION PIPELINE

Create a Python Function App:

Responsibilities:

1. Pull financial data from the API
2. Save raw JSON to Azure Blob Storage
3. Convert relevant fields into text documents
4. Attach metadata:

   * company
   * document type
   * year
5. Chunk text
6. Generate embeddings
7. Store in Chroma Cloud

---

VECTOR STORAGE

Use Chroma Cloud.

Each indexed chunk should include metadata:

company
source_type (profile, income_statement, ratios, news)
date

---

LANGGRAPH AGENT

Implement an agent that orchestrates tools.

Tools:

retrieve_docs(query)
retrieves relevant financial documents from Chroma

fetch_company_metrics(company)
returns structured financial metrics

run_basic_financial_checks(company)
performs simple deterministic checks such as:
- declining revenue
- high debt ratio
- falling margins

generate_analysis(context)
LLM summarizes findings and explains possible risks.

The agent workflow should:

1. retrieve relevant documents
2. fetch structured metrics
3. run financial checks
4. produce an explainable answer

---

EXAMPLE USER QUESTIONS

"Give me a quick financial health summary for Apple."

"Why might Nvidia's margins be changing?"

"Are there any financial risk signals for Microsoft?"

---

PROJECT STRUCTURE

demo/
app/
main.py
agent.py
tools.py
retriever.py
ingestion/
ingest_financial_data.py
embed_index.py
data/
raw/
config/
settings.py
requirements.txt
README.md

---

TECH STACK

Python
FastAPI
LangGraph
Chroma Cloud
OpenAI or Azure OpenAI
Azure Blob Storage
Streamlit or CLI UI

---

DELIVERABLES

Generate:

1. Complete project folder structure
2. All Python source files
3. Example .env configuration
4. requirements.txt
5. Instructions to run the ingestion pipeline
6. Instructions to run the demo

The project must be runnable locally with minimal setup.


in Azure always use InterviewDemoSubscription 
No     Subscription name          Subscription ID                       Tenant
-----  -------------------------  ------------------------------------  -----------------
[1]    InterviewDemoSubscription  7aec3ed0-7ec5-498e-9284-6f21c94def7d  Default Directory

and if you're createing a function app always use flex consumption
this is a demo, no need to go crazy, the point is to show the interviewer i can do the job
dungmai@Dungs-MacBook-Pro-2 ~/D/W/InterviewDemo> cd financial_agents/
dungmai@Dungs-MacBook-Pro-2 ~/D/W/I/financial_agents (main)> ls
dungmai@Dungs-MacBook-Pro-2 ~/D/W/I/financial_agents (main)> cd ..
dungmai@Dungs-MacBook-Pro-2 ~/D/W/InterviewDemo> cd ..
dungmai@Dungs-MacBook-Pro-2 ~/D/Work> cd InterviewDemo/financial_data
dungmai@Dungs-MacBook-Pro-2 ~/D/W/I/financial_data (main)> ls
SampleFunctionApp/

dungmai@Dungs-MacBook-Pro-2 ~/D/W/I/financial_data (main)> pwd
/Users/dungmai/Desktop/Work/InterviewDemo/financial_data

you got 2 repos to work with financial_agents for the langgraph and financial_data for the azure stuffs
Do let me know if u need me to run anything