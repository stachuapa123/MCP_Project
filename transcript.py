"""Save everything that happens in one agent run to a folder you can read.

Each run gets its own folder, for example:

    logs/2026-10-06_14-03-22_step3_ollama/
        transcript.md              <- everything in order, easiest to read
        01_mcp_list_tools.json
        02_llm_request.json        <- exactly what we gave the model's library
        03_llm_response.json       <- exactly what came back, token counts included
        04_mcp_call_tool.json
        ...

Every LLM request contains the *whole* conversation so far. Models don't
remember anything between requests, so the agent resends everything every
time. Compare 02_llm_request.json with the next request to see it grow.

Set TRANSCRIPTS_DIR in .env to save somewhere other than logs/.
"""

import dataclasses
import json
import os
from datetime import datetime
from pathlib import Path

_folder: Path | None = None
_count = 0


def start(name: str) -> Path:
    """Start a new folder for one agent run. Later log() calls write into it."""
    global _folder, _count
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    _folder = Path(os.environ.get("TRANSCRIPTS_DIR", "logs")) / f"{stamp}_{name}"
    _folder.mkdir(parents=True, exist_ok=True)
    _count = 0
    (_folder / "transcript.md").write_text(f"# Transcript: {name}\n\nStarted {datetime.now():%Y-%m-%d %H:%M:%S}\n")
    return _folder


def log(kind: str, data) -> None:
    """Save one event as a numbered JSON file and append it to transcript.md."""
    global _count
    if _folder is None:  # no run started (for example, in a test): do nothing
        return
    _count += 1
    text = json.dumps(to_json(data), indent=2, ensure_ascii=False)
    (_folder / f"{_count:02d}_{kind}.json").write_text(text + "\n")
    with open(_folder / "transcript.md", "a") as f:
        f.write(f"\n## {_count}. {kind}  ({datetime.now():%H:%M:%S})\n\n```json\n{text}\n```\n")


def to_json(value):
    """Turn library objects (Claude blocks, Gemini parts, Ollama messages...) into plain JSON."""
    # All three libraries use pydantic models. by_alias gives the field names
    # actually sent over the network (e.g. "structuredContent", not "structured_content").
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if dataclasses.is_dataclass(value):  # our own ToolCall / ToolResult
        return to_json(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {k: to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)
