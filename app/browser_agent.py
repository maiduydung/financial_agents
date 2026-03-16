"""LangGraph Browser Agent — browses the web to enrich financial data on demand."""

import logging
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from browser_use import Agent as BrowserAgent, Browser, BrowserConfig
from config.settings import OPENAI_API_KEY, OPENAI_MODEL
from app.enrichment import ingest_to_chroma

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Financial Research Browser Agent. Your job is to browse the web
to find financial information about companies and enrich our knowledge base.

You have two capabilities:
1. browse_and_extract — use a real browser to navigate to websites, search for financial data,
   and extract relevant text content
2. store_enrichment — take extracted text and store it in our vector database for future queries

Workflow:
1. Use browse_and_extract to search for and extract the requested financial information
2. Use store_enrichment to save the extracted data to our knowledge base
3. Summarize what you found and stored

Be thorough but focused. Extract factual financial data, earnings info, analyst reports,
SEC filings, news articles, and other relevant financial content."""


class BrowserAgentState(TypedDict):
    messages: Annotated[list, add_messages]


@tool
async def browse_and_extract(task: str) -> str:
    """Browse the web using a real browser to find and extract financial information.

    The browser can navigate pages, click links, fill search forms, and extract content.

    Args:
        task: Detailed description of what to search for and extract.
              Example: "Go to Yahoo Finance and find the latest earnings data for AAPL"
    """
    logger.info("🌐 Browser agent starting task: %s", task)

    browser = Browser(config=BrowserConfig(headless=True))

    agent = BrowserAgent(
        task=task,
        llm=ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY),
        browser=browser,
        max_actions_per_step=5,
    )

    try:
        result = await agent.run(max_steps=10)
        extracted = result.final_result() if result.final_result() else "No content extracted."
        logger.info("🌐 Browser extracted %d chars", len(extracted))
        return extracted
    except Exception as e:
        logger.error("❌ Browser agent failed: %s", e)
        return f"Browser extraction failed: {e}"
    finally:
        await browser.close()


@tool
def store_enrichment(text: str, company: str, source_type: str = "web", source_url: str = "") -> str:
    """Store extracted web content in the Chroma vector database for future retrieval.

    Args:
        text: The extracted text content to store.
        company: Company ticker symbol (e.g. AAPL, MSFT, NVDA).
        source_type: Type of source (e.g. web, sec_filing, earnings, news, analyst_report).
        source_url: URL where the data was found.
    """
    logger.info("💾 Storing enrichment for %s (type: %s)", company, source_type)
    n_chunks = ingest_to_chroma(
        text=text,
        company=company,
        source_type=source_type,
        source_url=source_url,
    )
    return f"✅ Stored {n_chunks} chunks for {company} (source: {source_type})"


tools = [browse_and_extract, store_enrichment]


def _get_llm():
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
    ).bind_tools(tools)


def agent_node(state: BrowserAgentState):
    """Call the LLM with current messages."""
    logger.info("🤖 Browser agent thinking...")
    llm = _get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_names = [tc["name"] for tc in response.tool_calls]
        logger.info("🔧 Browser agent calling tools: %s", tool_names)
    else:
        logger.info("💬 Browser agent producing final answer")
    return {"messages": [response]}


def should_continue(state: BrowserAgentState):
    """Check if the agent should call tools or finish."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_browser_graph():
    """Build the LangGraph browser agent workflow."""
    graph = StateGraph(BrowserAgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


browser_agent = build_browser_graph()


async def run_browser_agent(task: str) -> str:
    """Run the browser agent with a research task and return the summary."""
    logger.info("🏁 Starting browser agent: %s", task)
    initial_state = {"messages": [HumanMessage(content=task)]}
    result = await browser_agent.ainvoke(initial_state)
    logger.info("🏁 Browser agent finished — %d messages in chain", len(result["messages"]))
    return result["messages"][-1].content
