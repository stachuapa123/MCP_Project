# MCP_Project

A small, hands-on project for learning **LLM tools**, **agent loops** and the
**Model Context Protocol (MCP)**. It is built around a calculator, so the
tools stay out of the way and you can focus on the plumbing.

## The ideas, in plain words

**Tool.** An LLM can only produce text. A *tool* is a function you tell the
model about by giving it a name, a description and a JSON Schema for its
inputs. The model never runs the tool. It replies "please call `multiply` with
`a=17, b=23`", and **your code** runs the function and sends the result back.

**Agent loop.** Repeat until the model stops asking for tools:

```
ask the model ──► it asks for a tool? ──yes──► run the tool, add the result ──┐
      ▲                   │ no                                                │
      │                   ▼                                                   │
      │             final answer                                              │
      └───────────────────────────────────────────────────────────────────────┘
```

Small as it is, this loop is what "agentic" means: the model decides the next
step, your code carries it out, and the model sees the outcome.

**MCP.** In step 1 the tools are hard-wired into one program. MCP is a standard
protocol that moves them into a separate **server**. Any MCP **client** can ask
a server "what tools do you have?" (`list_tools`) and "run this one"
(`call_tool`). Write a tool once and every MCP-aware app can use it: your own
agent, Claude Code, Claude Desktop and others.

```
  Claude API  ◄──►  your agent (MCP client)  ◄── stdio ──►  MCP server (calculator)
```

## The project in three steps

| File | What it teaches |
|---|---|
| `calculator.py` | The plain functions. No AI and no MCP. |
| `step1_agent.py` | Tools described by hand in JSON Schema, plus a hand-written agent loop. |
| `step2_server.py` | The same functions exposed as an MCP server. The schemas are generated from type hints. |
| `step3_mcp_agent.py` | The step 1 loop, except the tools come from the MCP server. |
| `claude_client.py` | The single place that calls the Claude API. |
| `tests/` | Tests for every step. No API key needed. |

Read the files in that order. Each one starts with a docstring that points out
what to notice.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ANTHROPIC_API_KEY=sk-ant-...   # from https://console.anthropic.com
```

You need Python 3.10 or newer. The tests don't need an API key:

```bash
pytest
```

## Run it

```bash
python step1_agent.py "What is (17 * 23) + sqrt(144)?"
python step3_mcp_agent.py "What is 2 to the power of 10, divided by 4?"
```

Both scripts print each tool call as it happens, so you can watch the loop.
The output looks something like this (the model's exact steps vary):

```
Question: What is (17 * 23) + sqrt(144)?
  [tool] multiply({'a': 17, 'b': 23}) -> 391
  [tool] sqrt({'x': 144}) -> 12.0
  [tool] add({'a': 391, 'b': 12.0}) -> 403.0
Answer: (17 × 23) + √144 = 403
```

Try asking it to divide by zero and see how it handles the error.

### Use your server from other MCP apps

Because step 2 is a standard MCP server, other apps can use it too:

```bash
# Add it to Claude Code (run from this folder):
claude mcp add calculator -- python step2_server.py

# Or poke at it in a browser UI with the MCP Inspector (needs Node.js):
npx @modelcontextprotocol/inspector python step2_server.py
```

## Ideas for what to try next

1. **Add a tool.** Add `modulo` or `factorial` to `calculator.py`, then expose
   it in step 1 and step 2. Notice how much less work step 2 is.
2. **A smarter tool.** Add one `evaluate(expression)` tool that safely parses
   strings like `"(2+3)*4"` (hint: Python's `ast` module, never `eval`). Does
   Claude still use the small tools?
3. **A tool with state.** Add `store(name, value)` and `recall(name)` so the
   calculator has memory across calls.
4. **Different tools.** Write a second MCP server, for example a notes server
   that reads and writes text files, and point `step3_mcp_agent.py` at it. The
   agent code shouldn't need to change.
5. **Resources and prompts.** MCP servers can also offer *resources*
   (read-only data) and *prompts* (reusable templates). Add a resource that
   lists the calculator's constants (`pi`, `e`).
6. **Let the SDK run the loop.** The Anthropic SDK has a tool runner
   (`client.beta.messages.tool_runner`) that runs this loop for you. Rewrite
   step 1 with it once you understand the manual version.
7. **HTTP transport.** Run the server over HTTP instead of stdio, so a client
   on another machine can reach it.

## Links

- MCP docs: https://modelcontextprotocol.io
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Claude tool use guide: https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
