"""Step 2: expose the same calculator as an MCP server.

Run:  python step2_server.py
(It waits silently for an MCP client on stdin/stdout. Stop it with Ctrl+C.
 Step 3 starts it for you, so you rarely run it by hand.)

What to notice compared with step 1:
  - No hand-written JSON Schema. `@mcp.tool()` reads each function's type hints
    and docstring and builds the tool definition itself.
  - No Claude, no agent loop. A server only answers two questions from a client:
    "which tools do you have?" (list_tools) and "run this one" (call_tool).
  - Any MCP client can use this server: our step 3 agent, Claude Code,
    Claude Desktop, or other apps. That reuse is the point of MCP.
"""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

import calculator

mcp = MCPServer("calculator")


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers: a + b."""
    return calculator.add(a, b)


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract two numbers: a - b."""
    return calculator.subtract(a, b)


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers: a * b."""
    return calculator.multiply(a, b)


@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide two numbers: a / b. b must not be 0."""
    try:
        return calculator.divide(a, b)
    except ValueError as e:
        # ToolError sends our message to the client. Any other exception is
        # reported only as a generic "Error executing tool".
        raise ToolError(str(e)) from e


@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise base to exponent: base ** exponent."""
    return calculator.power(base, exponent)

@mcp.tool()
def factorial(x: int):
    try:
        return calculator.factorial(x)
    except ValueError as e:
        # ToolError sends our message to the client. Any other exception is
        # reported only as a generic "Error executing tool".
        raise ToolError(str(e)) from e


@mcp.tool()
def sqrt(x: int) -> int:
    """Square root of x. x must not be negative."""
    try:
        return calculator.sqrt(x)
    except ValueError as e:
        raise ToolError(str(e)) from e


if __name__ == "__main__":
    mcp.run()  # stdio transport: talk to the client over stdin/stdout
