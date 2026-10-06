"""Talking to Claude. Needs ANTHROPIC_API_KEY (get one at https://console.anthropic.com)."""

import os
import time

import anthropic

import transcript
from llm import SYSTEM_PROMPT, Reply, ToolCall, ToolResult

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")


class ClaudeChat:
    def __init__(self, tools: list[dict]):
        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
        # Claude takes our tool format as-is: name, description, input_schema.
        self.tools = tools
        # The whole conversation, resent on every request. Roles: user / assistant.
        self.messages = []

    def send(self, question: str) -> Reply:
        self.messages.append({"role": "user", "content": question})
        return self._ask()

    def send_tool_results(self, results: list[ToolResult]) -> Reply:
        # All results go back together in one user message, each tied to its
        # request by tool_use_id.
        self.messages.append({"role": "user", "content": [
            {
                "type": "tool_result",
                "tool_use_id": r.call.id,
                "content": r.output,
                "is_error": r.is_error,
            }
            for r in results
        ]})
        return self._ask()

    def _ask(self) -> Reply:
        request = dict(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=self.tools,
            messages=self.messages,
            # If a safety classifier declines the request, let the API retry it
            # on a suitable fallback model instead of failing.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        transcript.log("llm_request", request)
        started = time.monotonic()
        response = self.client.beta.messages.create(**request)
        transcript.log("llm_response", {"seconds": round(time.monotonic() - started, 2), "response": response})
        if response.stop_reason == "refusal":
            return Reply(text="Claude declined this request.")

        # Keep Claude's whole reply (text + tool_use blocks) in the history.
        self.messages.append({"role": "assistant", "content": response.content})

        return Reply(
            text="".join(b.text for b in response.content if b.type == "text"),
            tool_calls=[
                ToolCall(id=b.id, name=b.name, args=b.input)
                for b in response.content if b.type == "tool_use"
            ],
        )
