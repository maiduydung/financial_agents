"""Agent tools for the Financial Analyst Agent."""

import logging
import httpx
from langchain_core.tools import tool
from app.retriever import retrieve_docs as _retrieve
from config.settings import FMP_API_KEY, FMP_BASE_URL

logger = logging.getLogger(__name__)


@tool
def retrieve_docs(query: str, company: str | None = None) -> str:
    """Retrieve relevant financial documents from the vector database.

    Args:
        query: Search query describing what information you need.
        company: Optional company ticker to filter results (e.g. AAPL).
    """
    logger.info("📚 Retrieving docs — query='%s', company=%s", query, company)
    docs = _retrieve(query, company=company, n_results=5)
    if not docs:
        logger.warning("⚠️ No documents found")
        return "No relevant documents found."
    logger.info("📚 Retrieved %d documents", len(docs))
    parts = []
    for doc in docs:
        meta = doc["metadata"]
        parts.append(f"[{meta.get('company', '?')} | {meta.get('source_type', '?')} | {meta.get('date', '?')}]\n{doc['text']}")
    return "\n\n---\n\n".join(parts)


@tool
def fetch_company_metrics(company: str) -> str:
    """Fetch live structured financial metrics for a company from the FMP API.

    Args:
        company: Company ticker symbol (e.g. AAPL, MSFT, NVDA).
    """
    logger.info("📊 Fetching metrics for %s", company)
    url = f"{FMP_BASE_URL}/ratios?symbol={company}&limit=1&apikey={FMP_API_KEY}"
    resp = httpx.get(url, timeout=15)
    if resp.status_code != 200 or not resp.json():
        logger.warning("⚠️ Could not fetch metrics for %s (status=%d)", company, resp.status_code)
        return f"Could not fetch metrics for {company}."
    logger.info("📊 Got metrics for %s", company)

    r = resp.json()[0]
    return (
        f"{company} Latest Financial Metrics:\n"
        f"  Current Ratio: {r.get('currentRatio', 'N/A')}\n"
        f"  Debt/Equity: {r.get('debtEquityRatio', 'N/A')}\n"
        f"  ROE: {r.get('returnOnEquity', 'N/A')}\n"
        f"  ROA: {r.get('returnOnAssets', 'N/A')}\n"
        f"  Gross Margin: {r.get('grossProfitMargin', 'N/A')}\n"
        f"  Net Margin: {r.get('netProfitMargin', 'N/A')}\n"
        f"  P/E Ratio: {r.get('priceEarningsRatio', 'N/A')}\n"
        f"  Dividend Yield: {r.get('dividendYield', 'N/A')}"
    )


@tool
def run_basic_financial_checks(company: str) -> str:
    """Run simple deterministic financial health checks for a company.

    Checks for: declining revenue, high debt ratio, falling margins.

    Args:
        company: Company ticker symbol (e.g. AAPL).
    """
    logger.info("🏥 Running financial health checks for %s", company)
    income_url = f"{FMP_BASE_URL}/income-statement?symbol={company}&limit=3&apikey={FMP_API_KEY}"
    ratios_url = f"{FMP_BASE_URL}/ratios?symbol={company}&limit=3&apikey={FMP_API_KEY}"

    income_resp = httpx.get(income_url, timeout=15)
    ratios_resp = httpx.get(ratios_url, timeout=15)

    flags = []

    # Check revenue trend
    if income_resp.status_code == 200 and income_resp.json():
        statements = income_resp.json()
        revenues = [s.get("revenue", 0) for s in statements]
        if len(revenues) >= 2 and revenues[0] < revenues[1]:
            flags.append(f"⚠ Revenue declined: ${revenues[1]:,.0f} → ${revenues[0]:,.0f}")
        if len(revenues) >= 2 and revenues[0] >= revenues[1]:
            flags.append(f"✓ Revenue growing: ${revenues[1]:,.0f} → ${revenues[0]:,.0f}")

    # Check debt and margins
    if ratios_resp.status_code == 200 and ratios_resp.json():
        ratios = ratios_resp.json()
        latest = ratios[0]

        de = latest.get("debtEquityRatio", 0)
        if de and de > 2.0:
            flags.append(f"⚠ High debt/equity ratio: {de:.2f}")
        elif de:
            flags.append(f"✓ Debt/equity ratio acceptable: {de:.2f}")

        # Margin trend
        if len(ratios) >= 2:
            curr_margin = ratios[0].get("netProfitMargin", 0)
            prev_margin = ratios[1].get("netProfitMargin", 0)
            if curr_margin and prev_margin and curr_margin < prev_margin:
                flags.append(f"⚠ Net margin declining: {prev_margin:.2%} → {curr_margin:.2%}")
            elif curr_margin and prev_margin:
                flags.append(f"✓ Net margin stable/improving: {prev_margin:.2%} → {curr_margin:.2%}")

    if not flags:
        logger.warning("⚠️ No check data available for %s", company)
        return f"No financial check data available for {company}."

    logger.info("🏥 Health checks complete for %s — %d flags", company, len(flags))
    return f"Financial Health Checks for {company}:\n" + "\n".join(flags)


@tool
def generate_analysis(context: str) -> str:
    """Summarize financial findings and explain possible risks.

    This tool is called after gathering all relevant data. Pass in all the
    context collected from other tools.

    Args:
        context: Combined text from retrieved documents, metrics, and checks.
    """
    logger.info("🧪 Generating analysis (%d chars of context)", len(context))
    return f"Please synthesize the following financial data into a clear analysis:\n\n{context}"


def _get_tavily_client():
    from tavily import TavilyClient
    from config.settings import TAVILY_API_KEY
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not set")
    return TavilyClient(api_key=TAVILY_API_KEY)


def _ingest_text(text: str, company: str, source_type: str = "web") -> int:
    """Send extracted text to the ingestor service. Returns chunks stored."""
    from config.settings import INGESTOR_BASE_URL
    if not text or len(text) < 20:
        return 0
    try:
        resp = httpx.post(
            f"{INGESTOR_BASE_URL}/api/ingestLLMData",
            json={"text": text, "company": company.upper(), "source_type": source_type},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json().get("chunks_stored", 0)
        logger.warning("⚠️ Ingestor returned %d: %s", resp.status_code, resp.text)
    except httpx.ConnectError:
        logger.warning("⚠️ Ingestor unavailable at %s — skipping storage", INGESTOR_BASE_URL)
    except Exception as e:
        logger.warning("⚠️ Ingestor call failed: %s", e)
    return 0


@tool
def web_search(query: str, company: str) -> str:
    """Search the web for financial information using Tavily. Fast and cheap.

    Use this as the PRIMARY way to find information not in the vector database:
    recent news, earnings, analyst opinions, company info, SEC filings, etc.

    Args:
        query: Search query, e.g. "AAPL Q4 2025 earnings results"
        company: Company ticker or name for metadata (e.g. AAPL).
    """
    logger.info("🔍 Web search: %s (company=%s)", query, company)
    client = _get_tavily_client()
    response = client.search(query=query, max_results=5, include_answer=True)

    parts = []
    if response.get("answer"):
        parts.append(f"Summary: {response['answer']}")
    for r in response.get("results", []):
        parts.append(f"[{r.get('title', '')}]({r.get('url', '')})\n{r.get('content', '')}")

    extracted = "\n\n---\n\n".join(parts)
    logger.info("🔍 Tavily returned %d results (%d chars)", len(response.get("results", [])), len(extracted))

    if not extracted or len(extracted) < 20:
        return f"No web results found for '{query}'."

    n_chunks = _ingest_text(extracted, company)
    logger.info("✅ Web search done — %d chunks stored for %s", n_chunks, company)
    return extracted


@tool
def web_extract(url: str, company: str) -> str:
    """Extract and read the full content of a specific URL using Tavily.

    Use this when you have a specific URL (article, SEC filing, company page, Wikipedia, etc.)
    and want to read its full content. Much better than just a search snippet.

    Args:
        url: The URL to extract content from, e.g. "https://en.wikipedia.org/wiki/Apple_Inc."
        company: Company ticker or name for metadata (e.g. AAPL).
    """
    logger.info("📄 Extracting URL: %s (company=%s)", url, company)
    client = _get_tavily_client()
    response = client.extract(url)

    parts = []
    for r in response.get("results", []):
        parts.append(r.get("raw_content", "") or r.get("content", ""))

    extracted = "\n\n".join(parts)
    logger.info("📄 Extracted %d chars from %s", len(extracted), url)

    if not extracted or len(extracted) < 20:
        return f"Could not extract content from {url}."

    n_chunks = _ingest_text(extracted, company)
    logger.info("✅ URL extraction done — %d chunks stored for %s", n_chunks, company)
    return extracted[:3000] + ("..." if len(extracted) > 3000 else "")


@tool
def web_research(query: str, company: str) -> str:
    """Deep web research on a topic using Tavily. Use for complex questions that need
    multiple sources synthesized together (e.g. "What are the risks facing NVDA in 2026?").

    This is slower and more expensive than web_search — only use when a simple search
    isn't enough and you need a thorough, multi-source answer.

    Args:
        query: Research question, e.g. "What are analysts saying about MSFT cloud growth?"
        company: Company ticker or name for metadata (e.g. MSFT).
    """
    logger.info("🔬 Deep research: %s (company=%s)", query, company)
    client = _get_tavily_client()
    response = client.research(query=query)

    extracted = response.get("report", "") or response.get("answer", "") or str(response)
    logger.info("🔬 Research returned %d chars", len(extracted))

    if not extracted or len(extracted) < 20:
        return f"No research results for '{query}'."

    n_chunks = _ingest_text(extracted, company)
    logger.info("✅ Deep research done — %d chunks stored for %s", n_chunks, company)
    return extracted[:5000] + ("..." if len(extracted) > 5000 else "")
