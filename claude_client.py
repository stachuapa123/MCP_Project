"""One shared helper for sending a request to Claude.

Both agents (step 1 and step 3) call `ask_claude`. The interesting part of
each agent is the loop around this call, not the call itself, so the API
details live here.
"""

import anthropic

MODEL = "claude-opus-5-5"

SYSTEM_PROMPT = (
    "You are a helpful assistant with access to calculator tools. "
    "Use the tools for any arithmetic instead of computing in your head, "
    "then give the user a short final answer."
)

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def ask_claude(messages: list, tools: list):
    """Send the conversation so far plus the tool definitions; return Claude's reply."""
    return client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=messages,
        # If a safety classifier declines the request, let the API retry it on a
        # suitable fallback model instead of failing. Harmless for a calculator,
        # but a good default to know about.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
