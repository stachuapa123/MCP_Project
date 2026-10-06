"""Runs both agent loops end to end with a scripted fake model (no API key needed).

The fake first asks for one tool call, then answers with the tool's result,
which is the same shape of conversation a real model produces.
"""

import anyio

import step1_agent
import step3_mcp_agent
from llm import Reply, ToolCall


class FakeChat:
    def __init__(self, tool_name, tool_args):
        self.call = ToolCall(id="call_1", name=tool_name, args=tool_args)

    def send(self, question):
        return Reply(tool_calls=[self.call])

    def send_tool_results(self, results):
        return Reply(text=f"It is {results[0].output}.")


def test_step1_loop(monkeypatch):
    monkeypatch.setattr(step1_agent, "make_chat", lambda tools: FakeChat("multiply", {"a": 17, "b": 23}))
    assert step1_agent.run_agent("17 * 23?") == "It is 391."


def test_step3_loop_over_stdio(monkeypatch):
    # Starts step2_server.py as a real subprocess, just like running step 3 by hand.
    monkeypatch.setattr(step3_mcp_agent, "make_chat", lambda tools: FakeChat("power", {"base": 2, "exponent": 10}))
    assert anyio.run(step3_mcp_agent.run_agent, "2^10?") == "It is 1024.0."


def test_step3_saves_a_transcript(monkeypatch, tmp_path):
    monkeypatch.setenv("TRANSCRIPTS_DIR", str(tmp_path))
    monkeypatch.setattr(step3_mcp_agent, "make_chat", lambda tools: FakeChat("power", {"base": 2, "exponent": 10}))
    anyio.run(step3_mcp_agent.run_agent, "2^10?")

    [folder] = tmp_path.iterdir()
    files = sorted(p.name for p in folder.iterdir())
    assert files == [
        "01_question.json",
        "02_mcp_list_tools.json",
        "03_mcp_call_tool.json",
        "04_final_answer.json",
        "transcript.md",
    ]
    assert '"isError": false' in (folder / "03_mcp_call_tool.json").read_text()
