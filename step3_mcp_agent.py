"""Step 3: an agent that gets its tools from the MCP server in step 2.

Run:  python step3_mcp_agent.py "What is 2 to the power of 10, divided by 4?"
(Uses Claude by default. Set LLM_PROVIDER=gemini in .env to use Gemini.)

The agent loop is the same as in step 1. Only two things changed:
  1. The tool list is not written here. We ask the MCP server for it
     (list_tools) and turn it into the tool format the model expects.
  2. When the model asks for a tool, we don't call a Python function. We forward
     the request to the server (call_tool) and pass its answer back.

So this agent knows nothing about calculators, and the server knows nothing
about Claude or Gemini. Point the agent at a different MCP server and it gets
different tools with no code changes.
"""

import sys

import anyio
from mcp import Client, StdioServerParameters

from llm import ToolResult, make_chat

# How to start the server: run step2_server.py with the same Python as this script.
SERVER = StdioServerParameters(command=sys.executable, args=["step2_server.py"])


def mcp_tool_to_dict(tool) -> dict:
    """MCP describes a tool with the same three pieces the models need."""
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.input_schema,
    }


async def call_mcp_tool(mcp_client: Client, name: str, args: dict) -> tuple[str, bool]:
    """Ask the MCP server to run a tool. Returns (result text, is_error)."""
    result = await mcp_client.call_tool(name, args)
    text = "\n".join(block.text for block in result.content if block.type == "text")
    return text, result.is_error


async def run_agent(question: str, server=SERVER, max_turns: int = 10) -> str:
    # `async with` starts the server process and shuts it down when we're done.
    async with Client(server) as mcp_client:
        listed = await mcp_client.list_tools()
        tools = [mcp_tool_to_dict(t) for t in listed.tools]
        print(f"  [mcp] server offers: {', '.join(t['name'] for t in tools)}")

        chat = make_chat(tools)
        reply = chat.send(question)

        for _ in range(max_turns):
            if not reply.tool_calls:
                return reply.text

            results = []
            for call in reply.tool_calls:
                output, is_error = await call_mcp_tool(mcp_client, call.name, call.args)
                print(f"  [mcp] {call.name}({call.args}) -> {output}")
                results.append(ToolResult(call, output, is_error))
            reply = chat.send_tool_results(results)

        return "Stopped: too many tool-calling turns."


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is 2 to the power of 10, divided by 4?"
    print(f"Question: {question}")
    print(f"Answer: {anyio.run(run_agent, question)}")
