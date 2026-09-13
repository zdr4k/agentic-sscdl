"""IT helpdesk agent.

Spawns the MCP server as a subprocess over stdio, loads its tools,
and wires them into a LangGraph ReAct agent backed by a local Ollama
model. No API key needed; anyone cloning the repo can run it.

Requires Ollama running locally with the model pulled:
    ollama pull qwen2.5:7b-instruct

Can be run from anywhere; the MCP server path is resolved relative
to this file, not to the caller's current working directory.
    python agent.py
"""

import asyncio
import pathlib
import sys

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

OLLAMA_MODEL = "qwen2.5:7b-instruct"

# Resolved from this file's own location so the script works
# regardless of which directory you launch python from.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MCP_SERVER_PATH = REPO_ROOT / "mcp" / "server.py"

SYSTEM_PROMPT = """You are an internal IT helpdesk assistant.
Help employees with account status, tickets, and IT knowledge base questions.
Only use the tools available to you. Never guess information you can look up.
"""


def build_model() -> ChatOllama:
    return ChatOllama(model=OLLAMA_MODEL, temperature=0)


async def main() -> None:
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

    agent = create_react_agent(build_model(), tools, prompt=SYSTEM_PROMPT)

    print("IT Helpdesk Agent. Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        reply = result["messages"][-1].content
        print(f"Agent: {reply}\n")


if __name__ == "__main__":
    asyncio.run(main())