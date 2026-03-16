"""Streamlit UI for the Financial Analyst Agent."""

import streamlit as st
import httpx

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Financial Analyst Agent", page_icon="📊")
st.title("📊 Financial Analyst Agent")
st.caption("Ask questions about AAPL, MSFT, and NVDA")

# Example questions
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
    with st.spinner("Agent is analyzing..."):
        try:
            resp = httpx.post(f"{API_URL}/query", json={"question": question}, timeout=60)
            if resp.status_code == 200:
                st.markdown("### Answer")
                st.markdown(resp.json()["answer"])
            else:
                st.error(f"API error: {resp.status_code}")
        except httpx.ConnectError:
            st.error("Cannot connect to API. Make sure the FastAPI server is running on port 8000.")
