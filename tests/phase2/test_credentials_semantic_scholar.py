"""Tests for the Semantic Scholar API key support in llmxive.credentials.

Added by spec 005 — librarian agent. Covers:
  - load_semantic_scholar_key returns None pre-key
  - save+load roundtrip for the SS key alone
  - save_dartmouth_key + save_semantic_scholar_key both retained when written
    to the same file (merge-not-overwrite behavior; regression guard for the
    spec-005 refactor of save_dartmouth_key from full-overwrite to merge)
  - env var SEMANTIC_SCHOLAR_API_KEY beats credentials file value

Per Constitution Principle III: real filesystem (pytest tmp_path), no mocks.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmxive.credentials import (
    SEMANTIC_SCHOLAR_KEY_NAME,
    load_dartmouth_key,
    load_semantic_scholar_key,
    mask_key,
    save_dartmouth_key,
    save_semantic_scholar_key,
)


def test_ss_loader_returns_none_when_no_env_no_file(monkeypatch, tmp_path):
    """Fresh state: env unset + creds file absent → None."""
    monkeypatch.delenv(SEMANTIC_SCHOLAR_KEY_NAME, raising=False)
    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)
    monkeypatch.setattr(
        "llmxive.credentials.credentials_path",
        lambda: tmp_path / "credentials.toml",
    )
    assert load_semantic_scholar_key(prompt_if_missing=False) is None


def test_ss_save_and_load_roundtrip(monkeypatch, tmp_path):
    """Save → load returns the saved value."""
    monkeypatch.delenv(SEMANTIC_SCHOLAR_KEY_NAME, raising=False)
    creds_path = tmp_path / "credentials.toml"
    monkeypatch.setattr("llmxive.credentials.credentials_path", lambda: creds_path)

    save_semantic_scholar_key("ss-test-key-12345", path=creds_path)
    loaded = load_semantic_scholar_key(prompt_if_missing=False)
    assert loaded == "ss-test-key-12345"


def test_save_both_keys_merges_in_one_file(monkeypatch, tmp_path):
    """Saving Dartmouth then SS (or vice versa) into the same file preserves
    both keys — regression guard for the spec-005 refactor of
    save_dartmouth_key from overwrite to merge.
    """
    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)
    monkeypatch.delenv(SEMANTIC_SCHOLAR_KEY_NAME, raising=False)
    creds_path = tmp_path / "credentials.toml"
    monkeypatch.setattr("llmxive.credentials.credentials_path", lambda: creds_path)

    save_dartmouth_key("sk-dart-12345", path=creds_path)
    save_semantic_scholar_key("ss-12345", path=creds_path)

    # Both must load back.
    assert load_dartmouth_key(prompt_if_missing=False) == "sk-dart-12345"
    assert load_semantic_scholar_key(prompt_if_missing=False) == "ss-12345"

    # File contains both literal keys.
    contents = creds_path.read_text(encoding="utf-8")
    assert "dartmouth_chat_api_key" in contents
    assert "semantic_scholar_api_key" in contents


def test_save_in_reverse_order_also_merges(monkeypatch, tmp_path):
    """Same as above but save SS first, then Dartmouth — order independence."""
    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)
    monkeypatch.delenv(SEMANTIC_SCHOLAR_KEY_NAME, raising=False)
    creds_path = tmp_path / "credentials.toml"
    monkeypatch.setattr("llmxive.credentials.credentials_path", lambda: creds_path)

    save_semantic_scholar_key("ss-first", path=creds_path)
    save_dartmouth_key("sk-dart-second", path=creds_path)

    assert load_dartmouth_key(prompt_if_missing=False) == "sk-dart-second"
    assert load_semantic_scholar_key(prompt_if_missing=False) == "ss-first"


def test_env_var_beats_credentials_file(monkeypatch, tmp_path):
    """Resolution order: env var first, file second."""
    creds_path = tmp_path / "credentials.toml"
    monkeypatch.setattr("llmxive.credentials.credentials_path", lambda: creds_path)
    save_semantic_scholar_key("ss-from-file", path=creds_path)

    monkeypatch.setenv(SEMANTIC_SCHOLAR_KEY_NAME, "ss-from-env")
    assert load_semantic_scholar_key(prompt_if_missing=False) == "ss-from-env"


def test_ss_key_resave_overwrites_value_not_other_keys(monkeypatch, tmp_path):
    """Saving the SS key twice updates the value but doesn't disturb dartmouth."""
    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)
    monkeypatch.delenv(SEMANTIC_SCHOLAR_KEY_NAME, raising=False)
    creds_path = tmp_path / "credentials.toml"
    monkeypatch.setattr("llmxive.credentials.credentials_path", lambda: creds_path)

    save_dartmouth_key("sk-dart", path=creds_path)
    save_semantic_scholar_key("ss-v1", path=creds_path)
    save_semantic_scholar_key("ss-v2", path=creds_path)  # update

    assert load_semantic_scholar_key(prompt_if_missing=False) == "ss-v2"
    # Dartmouth key still intact after the SS update.
    assert load_dartmouth_key(prompt_if_missing=False) == "sk-dart"


def test_mask_key_handles_unset():
    """Sanity: mask_key on None / empty returns sentinel."""
    assert mask_key(None) == "(unset)"
    assert mask_key("") == "(unset)"
