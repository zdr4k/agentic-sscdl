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

## Security pipeline

| Workflow | Type | What it does | Trigger |
|---|---|---|---|
| `Codeql.yml` | SAST | CodeQL on Python and on the workflow files themselves. | PR, push to `main`, weekly |
| `synk-code.yml` | SAST | Snyk Code on the application code. | PR |
| `sca.yml` | SCA | Snyk on the `requirements.txt` dependencies. Results go to Code Scanning (SARIF). | PR touching `requirements.txt`, weekly |
| `zizmor.yml` | CI lint | Analyzes workflows for bad practices (permissions, injection, unpinned actions). | PR |
| `mcp-scan.yml` | MCP scan | Snyk Agent Scan on the MCP server's tools. | PR touching `mcp/**` |
| `promptfoo.yml` | DAST | Attacks the MCP tool directly with adversarial payloads, deterministic, no LLM. | PR touching `mcp/**`, `promptfooconfig.yaml` |

Practices applied in the workflows: `permissions: {}` at the top level with least-privilege permissions per job, `persist-credentials: false` on checkout, and actions pinned by SHA.

There used to be a second `promptfoo.yml` job that red-teamed the live agent in CI via GitHub Models, using the job's own `GITHUB_TOKEN` in place of an API key. GitHub Models was retired on 2026-07-30; that endpoint now returns a bare `OK` for every request. Running a 7B model on the runner's CPU instead would cost minutes per PR for a signal that's non-deterministic by nature anyway, so that red-team layer (`promptfoo.agent.yaml`, `agent/redteam_provider.py`) stays a local-only tool instead of a CI job, see below.

### Required secrets

- `SNYK_TOKEN`: used by the Snyk workflows.

## Running the security tests locally

```bash
python scripts/create_db.py

# 1. Direct attack on the MCP tool (no LLM)
npx -y promptfoo@latest eval -c promptfooconfig.yaml --no-cache

# 2. Red team of the real agent (local-only, needs Ollama; see above)
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
