"""Talking to a local model through Ollama. No API key and no cost.

Setup:
  1. Install Ollama from https://ollama.com and start it (the app, or `ollama serve`).
  2. Download a model that supports tools:  ollama pull qwen3
  3. In .env:  LLM_PROVIDER=ollama   (optional: OLLAMA_MODEL=..., OLLAMA_HOST=...)

Small local models are worse at using tools than Claude or Gemini. If the
model ignores the tools or calls them wrongly, try a bigger one.
"""

import os
import time

import ollama

import transcript
from llm import SYSTEM_PROMPT, Reply, ToolCall, ToolResult

# Any model tagged "tools" on https://ollama.com/search?c=tools works.
MODEL = os.environ.get("OLLAMA_MODEL", "qwen3")


class OllamaChat:
    def __init__(self, tools: list[dict]):
        # Talks to the Ollama app on this computer (http://localhost:11434),
        # or to OLLAMA_HOST if set.
        self.client = ollama.Client()
        # Ollama uses the OpenAI-style format: each tool is wrapped in
        # {"type": "function", "function": {...}} and the schema is `parameters`.
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in tools
        ]
        # The whole conversation, resent on every request. Unlike Claude and
        # Gemini, the system prompt is just the first message.
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def send(self, question: str) -> Reply:
        self.messages.append({"role": "user", "content": question})
        return self._ask()

    def send_tool_results(self, results: list[ToolResult]) -> Reply:
        # One "tool" message per result. Ollama's tool calls have no ids, so
        # results are matched to calls by tool name and order.
        for r in results:
            self.messages.append({
                "role": "tool",
                "tool_name": r.call.name,
                # There is no is_error flag, so we say it in the text.
                "content": f"Error: {r.output}" if r.is_error else r.output,
            })
        return self._ask()

    def _ask(self) -> Reply:
        request = dict(model=MODEL, messages=self.messages, tools=self.tools)
        transcript.log("llm_request", request)
        started = time.monotonic()
        # If Ollama isn't running, this raises a ConnectionError that says so.
        response = self.client.chat(**request)
        transcript.log("llm_response", {"seconds": round(time.monotonic() - started, 2), "response": response})

        # Keep the model's whole reply (text + tool calls) in the history.
        self.messages.append(response.message)

        return Reply(
            text=response.message.content or "",
            tool_calls=[
                # Our loop needs an id for each call, so we number them.
                ToolCall(id=f"call_{i}", name=c.function.name, args=dict(c.function.arguments))
                for i, c in enumerate(response.message.tool_calls or [])
            ],
        )
