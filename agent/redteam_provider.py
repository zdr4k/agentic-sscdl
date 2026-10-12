"""Promptfoo custom provider: red-teams the real agent, not the raw tool.

Each call rebuilds the agent (spawns the MCP server over stdio, wires
its tools into the LangGraph agent) and sends the prompt through it
exactly the way a user would, then hands the agent's reply text back
to promptfoo for assertions. Rebuilding per call costs a few seconds;
for the handful of red-team cases this file is matched against,
that's the right trade-off over caching a stdio subprocess across
calls from a provider promptfoo may or may not keep alive between
invocations.
"""

import asyncio
import pathlib
import sys

AGENT_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AGENT_DIR))

import agent as helpdesk_agent  # noqa: E402


def call_api(prompt, options, context):
    async def run() -> str:
        agent = await helpdesk_agent.build_agent()
        return await helpdesk_agent.ask(agent, prompt)

    return {"output": asyncio.run(run())}
