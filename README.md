# AppSec for AI Agents: IT Helpdesk

A study project that builds a simple AI agent (an IT helpdesk assistant) and wraps it in a complete security pipeline on GitHub Actions: SAST, SCA, workflow linting, MCP server scanning and red teaming of the agent.

The code contains an **intentional** vulnerability: `search_tickets` builds its SQL query with an f-string (SQL injection). It acts as the target that shows what each tool in the pipeline detects.

## Architecture

```
User ──► agent/agent.py (LangGraph ReAct) ──stdio──► mcp/server.py (FastMCP) ──► data/helpdesk.db (SQLite)
```

| Component | Description |
|---|---|
| `agent/agent.py` | LangGraph agent that spawns the MCP server as a subprocess and uses its tools. |
| `agent/redteam_provider.py` | promptfoo provider: sends the prompt through the real agent and returns its reply. |
| `mcp/server.py` | MCP server with two tools: `lookup_employee` and `search_tickets`. |
| `mcp/mock_data.py` | Fake employee records. |
| `scripts/create_db.py` | Creates and seeds the SQLite tickets database. |
| `promptfooconfig.yaml` | Tests against the MCP tool directly (no LLM). |
| `promptfoo.agent.yaml` | Red-team tests against the agent, in natural language. |
| `mcp-scan-config.json` | Configuration used by Snyk Agent Scan. |

## Running locally

Requirements: Python 3.12+ and [Ollama](https://ollama.com).

```bash
pip install -r requirements.txt
python scripts/create_db.py        # creates data/helpdesk.db
ollama pull qwen2.5:7b-instruct
python agent/agent.py
```

### Model backend

The same code picks its model through an environment variable:

| `LLM_BACKEND` | Model | Use |
|---|---|---|
| (unset) | Ollama `qwen2.5:7b-instruct` | Local, no API key. |
| `github` | GitHub Models `openai/gpt-4o-mini` | CI; uses the job's `GITHUB_TOKEN` (`GITHUB_TOKEN` must be set). |

## Security pipeline

| Workflow | Type | What it does | Trigger |
|---|---|---|---|
| `Codeql.yml` | SAST | CodeQL on Python and on the workflow files themselves. | PR, push to `main`, weekly |
| `synk-code.yml` | SAST | Snyk Code on the application code. | PR |
| `sca.yml` | SCA | Snyk on the `requirements.txt` dependencies. Results go to Code Scanning (SARIF). | PR touching `requirements.txt`, weekly |
| `zizmor.yml` | CI lint | Analyzes workflows for bad practices (permissions, injection, unpinned actions). | PR |
| `mcp-scan.yml` | MCP scan | Snyk Agent Scan on the MCP server's tools. | PR touching `mcp/**` |
| `promptfoo.yml` | DAST | Two jobs: attacks the MCP tool directly and red-teams the agent. | PR touching `mcp/**`, `agent/**`, `promptfoo*.yaml` |

Practices applied in the workflows: `permissions: {}` at the top level with least-privilege permissions per job, `persist-credentials: false` on checkout, and actions pinned by SHA.

### Required secrets

- `SNYK_TOKEN`: used by the Snyk workflows.
- `GITHUB_TOKEN`: already available in every job; the agent job only needs the `models: read` permission.

## Running the security tests locally

```bash
python scripts/create_db.py

# 1. Direct attack on the MCP tool (no LLM)
npx -y promptfoo@latest eval -c promptfooconfig.yaml --no-cache

# 2. Red team of the real agent (needs Ollama or LLM_BACKEND=github)
npx -y promptfoo@latest eval -c promptfoo.agent.yaml --no-cache

# 3. MCP server scan
uvx snyk-agent-scan@latest --ci --dangerously-run-mcp-servers ./mcp-scan-config.json
```

The tests cover boolean tautologies (`' OR '1'='1`), schema enumeration with `UNION SELECT` and instruction-override attempts, always paired with control cases confirming that legitimate searches still work.

With the current vulnerability, the attack tests **are expected to fail**. They pass once `search_tickets` uses a parameterized query:

```python
conn.execute("SELECT ... FROM tickets WHERE subject LIKE ?", (f"%{keyword}%",))
```

## Disclaimer

All data is fictional and the project is for educational purposes. Do not use the MCP server as-is in production.
