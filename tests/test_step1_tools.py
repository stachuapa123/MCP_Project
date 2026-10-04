"""Checks the step 1 tool plumbing without calling Claude."""

from step1_agent import FUNCTIONS, TOOLS, run_tool


def test_every_tool_has_a_function():
    assert {t["name"] for t in TOOLS} == set(FUNCTIONS)


def test_run_tool():
    assert run_tool("multiply", {"a": 17, "b": 23}) == ("391", False)


def test_run_tool_reports_errors():
    assert run_tool("divide", {"a": 1, "b": 0}) == ("Cannot divide by zero.", True)
    assert run_tool("modulo", {"a": 1, "b": 2}) == ("Unknown tool: modulo", True)
