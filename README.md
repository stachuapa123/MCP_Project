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
  Claude / Gemini / Ollama  ◄──►  your agent (MCP client)  ◄── stdio ──►  MCP server (calculator)
```

## The project in three steps

| File | What it teaches |
|---|---|
| `calculator.py` | The plain functions. No AI and no MCP. |
| `step1_agent.py` | Tools described by hand in JSON Schema, plus the agent loop. |
| `step2_server.py` | The same functions exposed as an MCP server. The schemas are generated from type hints. |
| `step3_mcp_agent.py` | The step 1 loop, except the tools come from the MCP server. |
| `llm.py` | Picks the model (Claude, Gemini or Ollama) and defines the small interface both agents use. |
| `chat_claude.py`, `chat_gemini.py`, `chat_ollama.py` | How each provider formats tools, tool calls and results. Compare them side by side. |
| `transcript.py` | Saves every request, response and tool call of a run to `logs/`. |
| `tests/` | Tests for every step. No API key needed. |

Read the files in that order. Each one starts with a docstring that points out
what to notice.

## Setup

You need Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                           # the tests don't need an API key
```

### API key and choice of model

The agents work with **Claude**, **Gemini** or a local model through
**Ollama**. Copy the example settings file and fill in what the one you want
needs:

```bash
cp .env.example .env
```

```
LLM_PROVIDER=claude              # or: gemini, ollama
ANTHROPIC_API_KEY=sk-ant-...     # for Claude: https://console.anthropic.com
GEMINI_API_KEY=...               # for Gemini: https://aistudio.google.com/apikey
```

You only need the key for the provider you pick. Gemini has a free tier, and
Ollama needs no key at all. The scripts read `.env` automatically.

### Running a local model with Ollama

[Ollama](https://ollama.com) runs open models on your own computer: free,
offline, and nothing leaves your machine.

1. Install Ollama from https://ollama.com and start it.
2. Download a model that can use tools: `ollama pull qwen3`
3. Set `LLM_PROVIDER=ollama` in `.env`.

Any model with the "tools" tag on https://ollama.com/search?c=tools works.
Set `OLLAMA_MODEL` to use a different one. Small models are noticeably worse
at using tools than Claude or Gemini, which is interesting to watch: try
the same question on each and compare.

**Never commit `.env`.** It holds your secret keys. It's already in
`.gitignore`, so git ignores it. If a key ever ends up on GitHub, delete it in
the provider's console and create a new one.

### Claude vs Gemini vs Ollama

The agent loop is identical for all three. Only the format details differ:

| Idea | Claude | Gemini | Ollama |
|---|---|---|---|
| Describing a tool | `{"name", "description", "input_schema"}` | `FunctionDeclaration(name, description, parameters_json_schema)` | `{"type": "function", "function": {"name", "description", "parameters"}}` |
| Model asks for a tool | `tool_use` block in `response.content` | `response.function_calls` | `response.message.tool_calls` |
| Sending the result back | `tool_result` block with `tool_use_id` | `FunctionResponse` with `id` and `name` | A `"tool"` message with `tool_name` |
| Reporting an error | `is_error: True` | Inside the response, e.g. `{"error": "..."}` | In the text, e.g. `"Error: ..."` |
| System prompt | `system=` parameter | `system_instruction` in the config | The first message, with role `system` |
| Message history | `messages`, roles `user` / `assistant` | `contents`, roles `user` / `model` | `messages`, roles `user` / `assistant` / `tool` |

Ollama's tool format is the same one OpenAI uses, so `chat_ollama.py` is
also a good starting point for an OpenAI version.

The MCP server (step 2) doesn't change at all when you switch models. MCP
servers don't know which model is on the other side.

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

### See every detail: the transcripts folder

Every run saves the whole conversation to its own folder in `logs/`:

```
logs/2026-10-06_14-03-22_step3_ollama/
    transcript.md              <- everything in order, easiest to read
    01_question.json
    02_mcp_list_tools.json     <- what the MCP server said it offers
    03_llm_request.json        <- exactly what was sent to the model
    04_llm_response.json       <- exactly what came back, with token counts
    05_mcp_call_tool.json      <- the tool call sent to the server, and its result
    ...
    11_final_answer.json
```

Things worth looking for:

- **The model has no memory.** Each `llm_request` contains the *whole*
  conversation so far: system prompt, tool list, question, every tool call
  and result. Compare two requests to see it grow.
- **Tool definitions are just text in the request.** Look at the `tools`
  field: that's all the model knows about your functions.
- **Token counts** are in each `llm_response`, so you can see what each step
  costs (`usage` for Claude, `usageMetadata` for Gemini, `prompt_eval_count`
  and `eval_count` for Ollama).
- **Each provider's format** is visible as-is, matching the comparison table
  above.

`logs/` is in `.gitignore`, so transcripts stay on your computer.

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
   the model still use the small tools?
3. **A tool with state.** Add `store(name, value)` and `recall(name)` so the
   calculator has memory across calls.
4. **Different tools.** Write a second MCP server, for example a notes server
   that reads and writes text files, and point `step3_mcp_agent.py` at it. The
   agent code shouldn't need to change.
5. **Resources and prompts.** MCP servers can also offer *resources*
   (read-only data) and *prompts* (reusable templates). Add a resource that
   lists the calculator's constants (`pi`, `e`).
6. **Let the SDK run the loop.** Both SDKs can run this loop for you: the
   Anthropic SDK's tool runner (`client.beta.messages.tool_runner`) and the
   Gemini SDK's automatic function calling. Try them once you understand the
   manual version.
7. **HTTP transport.** Run the server over HTTP instead of stdio, so a client
   on another machine can reach it.
8. **Another provider.** Add `chat_openai.py`. You only need to write one
   class with `send` and `send_tool_results`, and `chat_ollama.py` already
   uses the same tool format.

## Links

- MCP docs: https://modelcontextprotocol.io
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Claude tool use guide: https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
- Gemini function calling guide: https://ai.google.dev/gemini-api/docs/function-calling
- Ollama Python library (with tool-calling examples): https://github.com/ollama/ollama-python
