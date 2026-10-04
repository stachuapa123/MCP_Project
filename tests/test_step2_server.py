"""Talks to the MCP server in-process, the same way step 3 does, without calling Claude."""

import anyio
from mcp import Client

from step1_agent import TOOLS
from step2_server import mcp
from step3_mcp_agent import call_mcp_tool, mcp_tool_to_claude


def run(fn):
    async def main():
        async with Client(mcp) as client:
            return await fn(client)
    return anyio.run(main)


def test_server_lists_same_tools_as_step1():
    listed = run(lambda c: c.list_tools())
    assert {t.name for t in listed.tools} == {t["name"] for t in TOOLS}


def test_tools_convert_to_claude_format():
    listed = run(lambda c: c.list_tools())
    add = next(mcp_tool_to_claude(t) for t in listed.tools if t.name == "add")
    assert add["description"] == "Add two numbers: a + b."
    assert add["input_schema"]["required"] == ["a", "b"]


def test_call_tool():
    assert run(lambda c: call_mcp_tool(c, "add", {"a": 2, "b": 3})) == ("5.0", False)


def test_call_tool_error_message_reaches_client():
    text, is_error = run(lambda c: call_mcp_tool(c, "divide", {"a": 1, "b": 0}))
    assert is_error
    assert "Cannot divide by zero." in text
