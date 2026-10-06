"""Talking to Gemini. Needs GEMINI_API_KEY (get one at https://aistudio.google.com/apikey)."""

import os
import time

from google import genai
from google.genai import types

import transcript
from llm import SYSTEM_PROMPT, Reply, ToolCall, ToolResult

# Check Google's docs for the current model names and set GEMINI_MODEL to change it.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


class GeminiChat:
    def __init__(self, tools: list[dict]):
        self.client = genai.Client()  # reads GEMINI_API_KEY
        # Same information as for Claude, but Gemini calls the schema
        # `parameters_json_schema` and wraps the list in a Tool object.
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=[
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters_json_schema=t["input_schema"],
                )
                for t in tools
            ])],
        )
        # The whole conversation, resent on every request. Roles: user / model.
        self.contents = []

    def send(self, question: str) -> Reply:
        self.contents.append(types.Content(role="user", parts=[types.Part(text=question)]))
        return self._ask()

    def send_tool_results(self, results: list[ToolResult]) -> Reply:
        # Gemini has no is_error flag, so an error goes inside the response dict.
        self.contents.append(types.Content(role="user", parts=[
            types.Part(function_response=types.FunctionResponse(
                id=r.call.id,
                name=r.call.name,
                response={"error": r.output} if r.is_error else {"result": r.output},
            ))
            for r in results
        ]))
        return self._ask()

    def _ask(self) -> Reply:
        request = dict(model=MODEL, contents=self.contents, config=self.config)
        transcript.log("llm_request", request)
        started = time.monotonic()
        response = self.client.models.generate_content(**request)
        transcript.log("llm_response", {"seconds": round(time.monotonic() - started, 2), "response": response})
        if not response.candidates:
            return Reply(text="Gemini returned no answer (the request may have been blocked).")

        # Keep Gemini's whole reply (text + function calls) in the history.
        self.contents.append(response.candidates[0].content)

        parts = response.candidates[0].content.parts or []
        return Reply(
            text="".join(p.text for p in parts if p.text),
            tool_calls=[
                ToolCall(id=c.id, name=c.name, args=dict(c.args or {}))
                for c in response.function_calls or []
            ],
        )
