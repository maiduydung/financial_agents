"""Streamlit Chatbot UI for the Financial Analyst Agent."""

import json
import streamlit as st
import httpx

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Financial Analyst Agent", page_icon="📊", layout="wide")
st.title("📊 Financial Analyst Agent")
st.caption("Ask anything about AAPL, MSFT, NVDA — the agent decides what tools to use (RAG, live data, web browsing)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar with examples
with st.sidebar:
    st.markdown("### 💡 Try asking")
    examples = [
        "Give me a quick financial health summary for Apple.",
        "Why might Nvidia's margins be changing?",
        "Are there any financial risk signals for Microsoft?",
        "Find the latest earnings call highlights for NVDA and analyze them.",
        "What do analysts think about AAPL's stock price target?",
    ]
    for ex in examples:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state.pending_question = ex
            st.rerun()

    st.divider()
    st.markdown(
        "**How it works:**\n"
        "The agent orchestrator decides which tools to call:\n"
        "- 📚 Vector search (Chroma)\n"
        "- 📊 Live metrics (FMP API)\n"
        "- 🏥 Financial health checks\n"
        "- 🌐 Web browsing (if needed)\n"
        "- 🧪 Analysis synthesis\n\n"
        "If new data is found via browsing, it's automatically ingested into the knowledge base."
    )

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle pending question from sidebar button
if "pending_question" in st.session_state:
    prompt = st.session_state.pop("pending_question")
else:
    prompt = st.chat_input("Ask about a company...")

if prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response via SSE stream
    with st.chat_message("assistant"):
        log_container = st.status("🤖 Agent is working...", expanded=True)
        answer_placeholder = st.empty()
        answer = None

        try:
            with httpx.stream(
                "POST",
                f"{API_URL}/query/stream",
                json={
                    "question": prompt,
                    "history": st.session_state.messages[:-1],
                },
                timeout=600,
            ) as resp:
                for line in resp.iter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = json.loads(line[6:])
                    if payload["type"] == "log":
                        log_container.write(payload["message"])
                    elif payload["type"] == "answer":
                        answer = payload["message"]

            log_container.update(label="✅ Agent finished", state="complete", expanded=False)

            if answer:
                answer_placeholder.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                answer_placeholder.error("Agent returned no answer.")

        except httpx.ConnectError:
            log_container.update(label="❌ Connection failed", state="error")
            err = "Cannot connect to API. Make sure the FastAPI server is running on port 8000."
            answer_placeholder.error(err)
            st.session_state.messages.append({"role": "assistant", "content": err})
