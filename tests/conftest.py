import pytest


@pytest.fixture(autouse=True)
def transcripts_in_tmp(tmp_path, monkeypatch):
    """Keep test runs' transcripts out of the real logs/ folder."""
    monkeypatch.setenv("TRANSCRIPTS_DIR", str(tmp_path / "logs"))
