"""Pick which model the agents talk to: Claude, Gemini or a local Ollama model.

Both agents (step 1 and step 3) only use what is in this file:

    chat = make_chat(tools)              # tools: [{"name", "description", "input_schema"}]
    reply = chat.send(question)          # -> Reply
    reply = chat.send_tool_results(...)  # -> Reply

Each provider stores its tools and its message history in its own format
(see chat_claude.py, chat_gemini.py and chat_ollama.py). Put them side by
side to see that the ideas are the same and only the field names differ.

Choose the provider in .env with LLM_PROVIDER=claude (default), gemini or ollama.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()  # copy the values from .env into the environment

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to calculator tools. "
    "Use the tools for any arithmetic instead of computing in your head, "
    "then give the user a short final answer."
)


@dataclass
class ToolCall:
    """The model asking us to run one tool."""
    id: str
    name: str
    args: dict


@dataclass
class ToolResult:
    """Our answer to one ToolCall."""
    call: ToolCall
    output: str
    is_error: bool = False


@dataclass
class Reply:
    """One model response: either tool calls to run, or the final text."""
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


def provider_name() -> str:
    return os.environ.get("LLM_PROVIDER", "claude").lower()


def make_chat(tools: list[dict]):
    provider = provider_name()
    # Imported here so you only need the library for the provider you use.
    if provider == "claude":
        from chat_claude import ClaudeChat
        return ClaudeChat(tools)
    if provider == "gemini":
        from chat_gemini import GeminiChat
        return GeminiChat(tools)
    if provider == "ollama":
        from chat_ollama import OllamaChat
        return OllamaChat(tools)
    raise ValueError(f"Unknown LLM_PROVIDER {provider!r}: use 'claude', 'gemini' or 'ollama'.")
