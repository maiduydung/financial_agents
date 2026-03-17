"""Browser Agent — browses the web to enrich financial data on demand."""

import logging
from browser_use import Agent as BrowserAgent, Browser
from browser_use.llm import ChatOpenAI as BrowserChatOpenAI
from app.enrichment import ingest_to_chroma
from config.settings import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)


def _get_browser_llm():
    return BrowserChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY)


async def browse_and_extract(task: str) -> str:
    """Use a headless browser to search the web and extract content."""
    logger.info("🌐 Browser starting task: %s", task)

    browser = Browser(headless=True)

    agent = BrowserAgent(
        task=task,
        llm=_get_browser_llm(),
        browser=browser,
        max_actions_per_step=5,
        use_judge=False,  # Don't let the judge reject partial results
    )

    try:
        result = await agent.run(max_steps=8)
        # Accept whatever was extracted — partial is fine for enrichment
        extracted = result.final_result() if result.final_result() else ""

        # Also grab any accumulated history text if final_result is empty
        if not extracted and result.history:
            # Collect text from action results
            texts = []
            for h in result.history:
                if h.result and hasattr(h.result, 'extracted_content') and h.result.extracted_content:
                    texts.append(h.result.extracted_content)
            extracted = "\n\n".join(texts) if texts else "No content extracted."

        logger.info("🌐 Browser extracted %d chars", len(extracted))
        return extracted
    except Exception as e:
        logger.error("❌ Browser agent failed: %s", e)
        return f"Browser extraction failed: {e}"
    finally:
        try:
            await browser.stop()
        except Exception:
            pass


async def run_browser_enrich(task: str, company: str) -> str:
    """Browse the web, extract content, and store it in Chroma.

    Returns a summary of what was found and stored.
    """
    logger.info("🌐 Starting web enrichment for %s: %s", company, task)

    # 1. Browse and extract
    extracted = await browse_and_extract(task)

    if not extracted or len(extracted) < 20:
        return f"Could not extract meaningful web data for {company}."

    # 2. Store in Chroma
    n_chunks = ingest_to_chroma(
        text=extracted,
        company=company.upper(),
        source_type="web",
    )

    summary = (
        f"🌐 Web enrichment complete for {company}:\n"
        f"  - Extracted {len(extracted)} chars from the web\n"
        f"  - Stored {n_chunks} chunks in Chroma\n\n"
        f"Content preview: {extracted[:500]}..."
    )
    logger.info("✅ Web enrichment done for %s — %d chunks stored", company, n_chunks)
    return summary
