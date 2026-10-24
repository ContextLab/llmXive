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
    """
    Create a tiny validated_snippets.jsonl file with a single snippet.
    """
    snippet = {
        "snippet_id": "tiny-001",
        "code": "def add(a, b):\n    return a + b",
        "human_comment": "Adds two numbers.",
    }
    validated_path = paths.data("validated_snippets.jsonl")
    # Ensure the parent directories exist
    validated_path.parent.mkdir(parents=True, exist_ok=True)
    with validated_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(snippet) + "\n")
    yield

def test_load_validated_snippets(small_validated):
    snippets = _load_validated_snippets()
    assert isinstance(snippets, list)
    assert len(snippets) == 1
    assert snippets[0]["snippet_id"] == "tiny-001"

def test_tokenizer():
    enc = _tokenizer()
    # The tokenizer should have an encode method
    tokens = enc.encode("def foo(): pass")
    assert isinstance(tokens, list)

def test_truncate(monkeypatch):
    # Use a tokenizer with a very small max token count to force truncation
    class DummyEnc:
        def encode(self, txt):
            # 1 token per character for simplicity
            return list(txt)

        def decode(self, tokens):
            return "".join(tokens)

    dummy_enc = DummyEnc()
    # Monkeypatch the tokenizer to return our dummy encoder
    monkeypatch.setattr("src.data.generate_comments._tokenizer", lambda: dummy_enc)

    code = "line1\nline2\nline3\nline4"
    # MAX_TOKENS is 2048, but our dummy encoder will make this > limit if we set limit low
    # We'll temporarily set MAX_TOKENS to 10 via monkeypatch
    monkeypatch.setattr("src.data.generate_comments.MAX_TOKENS", 10)
    truncated = _truncate_to_token_limit(code, dummy_enc)
    # Expect truncation at a newline before exceeding 10 tokens
    assert truncated.endswith("\n")
    # Ensure the truncated version is shorter than the original
    assert len(truncated) < len(code)

def test_log_truncation(tmp_path: Path, monkeypatch):
    log_path = paths.data("truncation_warnings.log")
    # Ensure clean state
    if log_path.exists():
        log_path.unlink()
    _log_truncation("test-id", 2500, 2048)
    assert log_path.exists()
    content = log_path.read_text()
    assert "snippet_id=test-id" in content
    assert "original_tokens=2500" in content
    assert "truncated_tokens=2048" in content

def test_generate_llm_comment_failure(monkeypatch):
    # Ensure HF token is unset to trigger the RuntimeError
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        _generate_llm_comment("def foo(): pass")