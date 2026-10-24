import json
import os
from pathlib import Path

import pytest
from llmxive_toolkit import paths

from src.data.generate_comments import (
    _load_validated_snippets,
    _tokenizer,
    _truncate_to_token_limit,
    _log_truncation,
    _generate_llm_comment,
)

@pytest.fixture
def small_validated(tmp_path: Path, monkeypatch):
    """Create a tiny validated_snippets.jsonl file with a single snippet."""
    snippets = [
        {
            "snippet_id": "test-001",
            "code": "def add(a, b):\n    return a + b",
            "human_comment": "Adds two numbers together.",
        }
    ]
    data_path = paths.data("validated_snippets.jsonl")
    data_path.parent.mkdir(parents=True, exist_ok=True)
    with data_path.open("w", encoding="utf-8") as f:
        for rec in snippets:
            f.write(json.dumps(rec) + "\n")
    return snippets

def test_load_validated_snippets(small_validated):
    snippets = _load_validated_snippets()
    assert len(snippets) == 1
    assert snippets[0]["snippet_id"] == "test-001"

def test_tokenizer():
    enc = _tokenizer()
    assert hasattr(enc, "encode")
    assert hasattr(enc, "decode")

def test_truncate(monkeypatch):
    enc = _tokenizer()
    code = "a\n" * 5000  # many lines, will exceed token limit
    truncated = _truncate_to_token_limit(code, enc)
    assert len(enc.encode(truncated)) <= 2048

def test_log_truncation(tmp_path, monkeypatch):
    log_path = paths.data("truncation_warnings.log")
    if log_path.exists():
        log_path.unlink()
    _log_truncation("test-001", 3000, 2048)
    assert log_path.read_text().startswith("snippet_id=test-001")

def test_generate_llm_comment_failure(monkeypatch):
    """When HF token is missing, the function should raise RuntimeError."""
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        _generate_llm_comment("def foo(): pass")