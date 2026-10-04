"""Runs both agent loops end to end with a scripted fake Claude (no API key needed).

The fake first asks for one tool call, then gives a final answer, which is
the same shape of conversation the real model produces.
"""

from types import SimpleNamespace

import anyio

import step1_agent
import step3_mcp_agent


def fake_claude(tool_name, tool_input):
    def ask(messages, tools):
        if len(messages) == 1:  # first turn: request a tool
            block = SimpleNamespace(type="tool_use", id="call_1", name=tool_name, input=tool_input)
            return SimpleNamespace(stop_reason="tool_use", content=[block])
        result = messages[-1]["content"][0]  # second turn: echo the tool result
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=f"It is {result['content']}.")])
    return ask


def test_step1_loop(monkeypatch):
    monkeypatch.setattr(step1_agent, "ask_claude", fake_claude("multiply", {"a": 17, "b": 23}))
    assert step1_agent.run_agent("17 * 23?") == "It is 391."


def test_step3_loop_over_stdio(monkeypatch):
    # Starts step2_server.py as a real subprocess, just like running step 3 by hand.
    monkeypatch.setattr(step3_mcp_agent, "ask_claude", fake_claude("power", {"base": 2, "exponent": 10}))
    assert anyio.run(step3_mcp_agent.run_agent, "2^10?") == "It is 1024.0."
