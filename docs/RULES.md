# AI Instance Governance Rules
### These RULES must be followed at all times.

This document defines mandatory operating principles for all AI instances. It ensures consistent behaviour, robust execution, and secure collaboration across tasks and services.

---

## Code Quality Standards

- All modules must implement structured error handling with specific failure modes.
- Every function must include a concise, purpose-driven docstring.
- Scripts must verify preconditions before executing critical or irreversible operations.
- Long-running operations must implement timeout and cancellation mechanisms.
- File and path operations must verify existence and permissions before access.
- For API calls and I/O processes, always prioritize async.
- Prioritize OOP — use classes and methods for readability.
- No files should be longer than 300 lines. If a file exceeds this, split into multiple classes in separate files.
- Agent nodes must be stateless — all shared state flows through the LangGraph state object.
- Never hardcode API keys, connection strings, or credentials. Always load from environment variables via `dotenv`.

---

## Documentation Protocols

- Keep documentation simple and easy to understand.
- Only update documentation in `/docs`, `CHANGELOG.md`, or `README.md` in the project root.
- Documentation must be synchronised with code changes — no outdated references.
- Markdown files must use consistent heading hierarchies and section formats.
- Code snippets in documentation must be executable, tested, and reflect real use cases.
- Each doc must clearly outline: purpose, usage, parameters, and examples.
- Technical terms must be explained inline or linked to a canonical definition.

---

## Agent Architecture Rules

- Each agent node must have a single, well-defined responsibility.
- Routing and tool selection logic must be deterministic where possible — use structured tool calls, not free-form LLM output.
- LLM calls are reserved for reasoning, analysis, and natural language generation — not control flow.
- All agent decisions must be logged with enough context to reproduce the decision path.
- RAG retrieval must specify `k` limits and relevance thresholds to avoid unbounded memory usage.
- Financial data from external APIs (FMP, Tavily) must be validated before ingestion — never trust raw responses blindly.
- SSE streaming responses must handle client disconnection gracefully.

---

## Process Execution Requirements

- Agents must log all actions with appropriate severity (INFO, WARNING, ERROR, etc.).
- Any failed task must include a clear, human-readable error report with traceback.
- Agents must respect system resource limits — especially memory, CPU usage, and timeout constraints.
- Long-running tasks must expose progress indicators or checkpoints.
- Retry logic must include exponential backoff and failure limits.
- API rate limits must be respected — implement throttling for external data providers.
