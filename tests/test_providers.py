"""Checks that each provider translates to and from its own format.

The real API is replaced by a fake that asks for one tool call and then
answers using the tool result it was sent, so no API key is needed.
"""

from types import SimpleNamespace

import pytest
from google.genai import types

from chat_claude import ClaudeChat
from chat_gemini import GeminiChat
from llm import ToolResult
from step1_agent import TOOLS


@pytest.fixture(autouse=True)
def fake_keys(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


def test_claude_chat():
    def create(messages, **kwargs):
        if len(messages) == 1:
            block = SimpleNamespace(type="tool_use", id="toolu_1", name="multiply", input={"a": 17, "b": 23})
            return SimpleNamespace(stop_reason="tool_use", content=[block])
        result = messages[-1]["content"][0]
        assert result["tool_use_id"] == "toolu_1"
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=f"It is {result['content']}.")])

    chat = ClaudeChat(TOOLS)
    chat.client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=create)))

    reply = chat.send("17 * 23?")
    [call] = reply.tool_calls
    assert (call.name, call.args) == ("multiply", {"a": 17, "b": 23})

    reply = chat.send_tool_results([ToolResult(call, "391")])
    assert reply.text == "It is 391."
    assert reply.tool_calls == []


def test_claude_refusal():
    chat = ClaudeChat(TOOLS)
    refusal = SimpleNamespace(stop_reason="refusal", content=[])
    chat.client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: refusal)))
    assert chat.send("hi").text == "Claude declined this request."


def gemini_response(part):
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(role="model", parts=[part]))]
    )


def test_gemini_chat():
    def generate_content(model, contents, config):
        assert {f.name for f in config.tools[0].function_declarations} == {t["name"] for t in TOOLS}
        if len(contents) == 1:
            call = types.FunctionCall(id="fc_1", name="multiply", args={"a": 17, "b": 23})
            return gemini_response(types.Part(function_call=call))
        response = contents[-1].parts[0].function_response
        assert (response.id, response.name) == ("fc_1", "multiply")
        return gemini_response(types.Part(text=f"It is {response.response['result']}."))

    chat = GeminiChat(TOOLS)
    chat.client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))

    reply = chat.send("17 * 23?")
    [call] = reply.tool_calls
    assert (call.name, call.args) == ("multiply", {"a": 17, "b": 23})

    reply = chat.send_tool_results([ToolResult(call, "391")])
    assert reply.text == "It is 391."
    assert reply.tool_calls == []


def test_gemini_errors_go_in_the_response():
    sent = []

    def generate_content(model, contents, config):
        sent.append(contents[-1])
        return gemini_response(types.Part(text="Sorry."))

    chat = GeminiChat(TOOLS)
    chat.client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    call = SimpleNamespace(id="fc_1", name="divide")
    chat.send_tool_results([ToolResult(call, "Cannot divide by zero.", is_error=True)])
    assert sent[-1].parts[0].function_response.response == {"error": "Cannot divide by zero."}


def test_ollama_chat():
    """Uses a fake Ollama server, so the real request and response formats are checked."""
    import json

    import httpx
    import ollama

    from chat_ollama import OllamaChat

    requests = []

    def fake_ollama_server(request):
        body = json.loads(request.content)
        requests.append(body)
        if len(body["messages"]) == 2:  # system + question: ask for a tool
            message = {"role": "assistant", "content": "", "tool_calls": [
                {"function": {"name": "multiply", "arguments": {"a": 17, "b": 23}}},
            ]}
        else:
            message = {"role": "assistant", "content": f"It is {body['messages'][-1]['content']}."}
        return httpx.Response(200, json={"model": "qwen3", "message": message, "done": True})

    chat = OllamaChat(TOOLS)
    chat.client = ollama.Client(transport=httpx.MockTransport(fake_ollama_server))

    reply = chat.send("17 * 23?")
    [call] = reply.tool_calls
    assert (call.name, call.args) == ("multiply", {"a": 17, "b": 23})
    tool = requests[0]["tools"][0]["function"]
    assert (tool["name"], tool["parameters"]["required"]) == ("add", ["a", "b"])

    reply = chat.send_tool_results([ToolResult(call, "391")])
    assert reply.text == "It is 391."
    assert requests[1]["messages"][-1] == {"role": "tool", "tool_name": "multiply", "content": "391"}

    chat.send_tool_results([ToolResult(call, "Cannot divide by zero.", is_error=True)])
    assert requests[2]["messages"][-1]["content"] == "Error: Cannot divide by zero."
