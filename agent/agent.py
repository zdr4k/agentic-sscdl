"""IT helpdesk agent.

Spawns the MCP server as a subprocess over stdio, loads its tools,
and wires them into a LangGraph ReAct agent.

Model backend is an environment switch, not a fork: local runs use
Ollama, free and with no API key, so anyone cloning the repo can try
it. In CI there's no GPU and no daemon worth standing up, so the
same agent code points at GitHub Models instead, using the
GITHUB_TOKEN every Actions job already has.

Local:
    ollama pull qwen2.5:7b-instruct
    python agent.py

CI (set by the workflow, not by hand):
    LLM_BACKEND=github GITHUB_TOKEN=... python agent.py
"""

import asyncio
import os
import pathlib
import sys

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

OLLAMA_MODEL = "qwen2.5:7b-instruct"
GITHUB_MODELS_ENDPOINT = "https://models.github.ai/inference"
GITHUB_MODEL = "openai/gpt-4o-mini"

# Resolved from this file's own location so the script works
# regardless of which directory you launch python from.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MCP_SERVER_PATH = REPO_ROOT / "mcp" / "server.py"

SYSTEM_PROMPT = """You are an internal IT helpdesk assistant.
Help employees with account status, tickets, and IT knowledge base questions.
Only use the tools available to you. Never guess information you can look up.
"""


def build_model():
    if os.environ.get("LLM_BACKEND") == "github":
        return ChatOpenAI(
            base_url=GITHUB_MODELS_ENDPOINT,
            api_key=os.environ["GITHUB_TOKEN"],
            model=GITHUB_MODEL,
            temperature=0,
        )
    return ChatOllama(model=OLLAMA_MODEL, temperature=0)


async def build_agent():
    """Construct the agent once: spawns the MCP server, loads its
    tools, and wires everything into a LangGraph ReAct agent.

    Split out from main() so anything else that needs to send a
    prompt through this exact agent, a test script, a red-team
    target, a notebook, can reuse it instead of re-implementing the
    setup.
    """
    # This spawns server/server.py as a child process. The agent
    # only ever "sees" the tool schemas the server exposes, not the
    # server's source code, which matters later when we start
    # scanning tool descriptions instead of trusting them.
    client = MultiServerMCPClient(
        {
            "it-helpdesk": {
                "command": sys.executable,
                "args": [str(MCP_SERVER_PATH)],
                "transport": "stdio",
            }
        }
    )
    tools = await client.get_tools()
    return create_agent(build_model(), tools, system_prompt=SYSTEM_PROMPT)


async def ask(agent, query: str) -> str:
    """Send one query through the agent and return its text reply."""
    result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].content


async def main() -> None:
    agent = await build_agent()

    print("IT Helpdesk Agent. Type 'exit' to quit.\n")
    while True:
        # Read on a worker thread. On Windows, blocking the main
        # thread on input() after asyncio has spawned a stdio
        # subprocess can leave the console's stdin handle returning
        # EOF on the next read.
        user_input = (await asyncio.to_thread(input, "You: ")).strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        reply = await ask(agent, user_input)
        print(f"Agent: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())