"""Step 1: give the model tools directly, with no MCP involved.

Run:  python step1_agent.py "What is (17 * 23) + sqrt(144)?"
(Uses Claude by default. Set LLM_PROVIDER=gemini in .env to use Gemini.)

What to notice:
  1. TOOLS describes each function to the model as JSON Schema. The model never
     sees the Python code, only the name, description and input schema.
  2. The model does not run anything. It replies "please call `multiply` with
     a=17, b=23". *Our* code runs the function.
  3. We send the answer back and ask again. Repeating that until the model
     stops asking for tools is the "agent loop".

How each provider formats tools and messages is in chat_claude.py and
chat_gemini.py. The loop below is the same for both.
"""

import sys

import calculator
from llm import ToolResult, make_chat


def number_tool(name: str, description: str, *params: str) -> dict:
    """Build a tool definition whose parameters are all numbers."""
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {p: {"type": "number"} for p in params},
            "required": list(params),
        },
    }


# What the model is told about each tool.
TOOLS = [
    number_tool("add", "Add two numbers: a + b.", "a", "b"),
    number_tool("subtract", "Subtract two numbers: a - b.", "a", "b"),
    number_tool("multiply", "Multiply two numbers: a * b.", "a", "b"),
    number_tool("divide", "Divide two numbers: a / b. b must not be 0.", "a", "b"),
    number_tool("power", "Raise base to exponent: base ** exponent.", "base", "exponent"),
    number_tool("sqrt", "Square root of x. x must not be negative.", "x"),
]

# Which Python function actually runs for each tool name.
FUNCTIONS = {
    "add": calculator.add,
    "subtract": calculator.subtract,
    "multiply": calculator.multiply,
    "divide": calculator.divide,
    "power": calculator.power,
    "sqrt": calculator.sqrt,
}


def run_tool(name: str, args: dict) -> tuple[str, bool]:
    """Run one tool. Returns (result text, is_error)."""
    if name not in FUNCTIONS:
        return f"Unknown tool: {name}", True
    try:
        return str(FUNCTIONS[name](**args)), False
    except (ValueError, TypeError) as e:
        # Errors go back to the model as a result, so it can recover or explain.
        return str(e), True


def run_agent(question: str, max_turns: int = 10) -> str:
    chat = make_chat(TOOLS)
    reply = chat.send(question)

    for _ in range(max_turns):
        if not reply.tool_calls:
            return reply.text  # no tools requested: this is the final answer

        # The model may ask for several tools at once. Run them all and send
        # every result back together.
        results = []
        for call in reply.tool_calls:
            output, is_error = run_tool(call.name, call.args)
            print(f"  [tool] {call.name}({call.args}) -> {output}")
            results.append(ToolResult(call, output, is_error))
        reply = chat.send_tool_results(results)

    return "Stopped: too many tool-calling turns."


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is (17 * 23) + sqrt(144)?"
    print(f"Question: {question}")
    print(f"Answer: {run_agent(question)}")
