"""Step 1: give Claude tools directly, with no MCP involved.

Run:  python step1_agent.py "What is (17 * 23) + sqrt(144)?"

What to notice:
  1. TOOLS describes each function to Claude as JSON Schema. Claude never sees
     the Python code, only the name, description and input schema.
  2. Claude does not run anything. It replies with a `tool_use` block that says
     "please call `multiply` with a=17, b=23". *Our* code runs the function.
  3. We send the answer back as a `tool_result` and ask again. Repeating that
     until Claude stops asking for tools is the "agent loop".
"""

import sys

import calculator
from claude_client import ask_claude


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


# What Claude is told about each tool.
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
        # Errors go back to Claude as a result, so it can recover or explain.
        return str(e), True


def run_agent(question: str, max_turns: int = 10) -> str:
    messages = [{"role": "user", "content": question}]

    for _ in range(max_turns):
        response = ask_claude(messages, TOOLS)

        if response.stop_reason == "refusal":
            return "Claude declined this request."

        # Keep Claude's whole reply (text + tool_use blocks) in the history.
        messages.append({"role": "assistant", "content": response.content})

        tool_calls = [block for block in response.content if block.type == "tool_use"]
        if not tool_calls:
            # No tools requested: this is the final answer.
            return "".join(block.text for block in response.content if block.type == "text")

        # Claude may ask for several tools at once. Run them all and send every
        # result back in a single user message.
        results = []
        for call in tool_calls:
            output, is_error = run_tool(call.name, call.input)
            print(f"  [tool] {call.name}({call.input}) -> {output}")
            results.append({
                "type": "tool_result",
                "tool_use_id": call.id,  # ties this result to Claude's request
                "content": output,
                "is_error": is_error,
            })
        messages.append({"role": "user", "content": results})

    return "Stopped: too many tool-calling turns."


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is (17 * 23) + sqrt(144)?"
    print(f"Question: {question}")
    print(f"Answer: {run_agent(question)}")
