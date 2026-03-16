"""Agent tools for the Financial Analyst Agent."""

import logging
import asyncio
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


@tool
def web_enrich(task: str, company: str) -> str:
    """Browse the web to find additional financial information and store it in the knowledge base.

    Use this when you need information that isn't available in the vector database or FMP API,
    such as recent news, SEC filings, analyst opinions, or earnings call details.

    Args:
        task: What to search for, e.g. "Find latest AAPL earnings call highlights"
        company: Company ticker symbol (e.g. AAPL).
    """
    from app.browser_agent import run_browser_agent

    logger.info("🌐 Web enrichment requested: %s (company=%s)", task, company)
    enriched_task = f"{task}. After extracting the information, store it for company {company}."

    # Run the browser agent
    loop = asyncio.get_event_loop()
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, run_browser_agent(enriched_task)).result()
    else:
        result = asyncio.run(run_browser_agent(enriched_task))

    logger.info("🌐 Web enrichment complete for %s", company)
    return result
