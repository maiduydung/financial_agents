"""Streamlit UI for the Financial Analyst Agent."""

import streamlit as st
import httpx

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Financial Analyst Agent", page_icon="📊", layout="wide")
st.title("📊 Financial Analyst Agent")
st.caption("Ask questions about AAPL, MSFT, and NVDA — powered by RAG + live data + web browsing")

tab_query, tab_enrich = st.tabs(["🤖 Ask Agent", "🌐 Web Enrichment"])

with tab_query:
    examples = [
        "Give me a quick financial health summary for Apple.",
        "Why might Nvidia's margins be changing?",
        "Are there any financial risk signals for Microsoft?",
    ]

    st.markdown("**Example questions:**")
    for ex in examples:
        if st.button(ex, key=ex):
            st.session_state["question"] = ex

    question = st.text_input("Your question:", value=st.session_state.get("question", ""), key="input")

    if st.button("Ask Agent", type="primary") and question:
        with st.spinner("🤖 Agent is analyzing..."):
            try:
                resp = httpx.post(f"{API_URL}/query", json={"question": question}, timeout=120)
                if resp.status_code == 200:
                    st.markdown("### Answer")
                    st.markdown(resp.json()["answer"])
                else:
                    st.error(f"API error: {resp.status_code}")
            except httpx.ConnectError:
                st.error("Cannot connect to API. Make sure the FastAPI server is running on port 8000.")

with tab_enrich:
    st.markdown(
        "Use the browser agent to research financial data on the web and "
        "automatically add it to the knowledge base."
    )

    enrich_examples = [
        "Find the latest AAPL earnings call highlights and key takeaways",
        "Search for recent analyst ratings and price targets for NVDA",
        "Look up Microsoft's latest SEC 10-K filing summary",
    ]

    st.markdown("**Example tasks:**")
    for ex in enrich_examples:
        if st.button(ex, key=f"enrich_{ex}"):
            st.session_state["enrich_task"] = ex

    task = st.text_input("Research task:", value=st.session_state.get("enrich_task", ""), key="enrich_input")

    if st.button("🌐 Browse & Enrich", type="primary") and task:
        with st.spinner("🌐 Browser agent is researching..."):
            try:
                resp = httpx.post(f"{API_URL}/enrich", json={"task": task}, timeout=300)
                if resp.status_code == 200:
                    st.markdown("### Enrichment Summary")
                    st.markdown(resp.json()["summary"])
                    st.success("Data has been added to the knowledge base!")
                else:
                    st.error(f"API error: {resp.status_code}")
            except httpx.ConnectError:
                st.error("Cannot connect to API. Make sure the FastAPI server is running on port 8000.")
