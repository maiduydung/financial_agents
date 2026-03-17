"""LangGraph Financial Analyst Agent."""

import logging
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from app.tools import retrieve_docs, fetch_company_metrics, run_basic_financial_checks, generate_analysis, web_search, web_extract, web_research
from config.settings import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a Financial Analyst Agent. Your job is to answer questions about companies
by using the tools available to you. Follow this workflow:

1. First, retrieve relevant documents from the vector database using retrieve_docs
2. For public companies: fetch live metrics (fetch_company_metrics) and health checks (run_basic_financial_checks)
3. Use web tools to supplement — they are fast and cheap, so use them freely:
   - web_search: Quick search for news, earnings, company info. Use this often.
   - web_extract: Read the full content of a specific URL (article, SEC filing, wiki page, etc.)
   - web_research: Deep multi-source research for complex questions. Slower — use when a simple search isn't enough.
4. Synthesize all findings into a clear, explainable analysis

GUIDELINES:
- Steps 2 only works for publicly traded companies with ticker symbols. Private companies will fail — that's expected.
- web_search is cheap and fast — prefer it whenever you need info beyond what's in the vector DB.
- If web_search returns a promising URL, use web_extract to read the full page.
- Use web_research only for complex, multi-faceted questions that need deep analysis.
- All web results are automatically stored in the knowledge base for future queries.

Always cite your sources (which documents/metrics you used). Be concise but thorough.
If you can identify the company ticker from the question, use it to filter results."""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


tools = [retrieve_docs, fetch_company_metrics, run_basic_financial_checks, generate_analysis, web_search, web_extract, web_research]


def _get_llm():
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0,
    ).bind_tools(tools)


def agent_node(state: AgentState):
    """Call the LLM with current messages."""
    logger.info("🤖 Agent thinking...")
    llm = _get_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_names = [tc["name"] for tc in response.tool_calls]
        logger.info("🔧 Agent calling tools: %s", tool_names)
    else:
        logger.info("💬 Agent producing final answer")
    return {"messages": [response]}


def should_continue(state: AgentState):
    """Check if the agent should call tools or finish."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def build_graph():
    """Build the LangGraph agent workflow."""
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Singleton compiled graph
agent = build_graph()


async def run_agent(question: str, history: list[tuple[str, str]] | None = None) -> str:
    """Run the agent with a user question and return the final answer."""
    logger.info("🏁 Starting agent for question: %s", question)
    messages = []
    for role, content in (history or []):
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=question))
    initial_state = {"messages": messages}
    result = await agent.ainvoke(initial_state)
    logger.info("🏁 Agent finished — %d messages in chain", len(result["messages"]))
    return result["messages"][-1].content
