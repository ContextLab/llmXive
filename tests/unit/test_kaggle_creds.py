"""Kaggle creds resolve from the SAME credentials.toml as the Dartmouth key.

The GPU-offload lane (#367) previously only read KAGGLE_* env vars / ~/.kaggle/
kaggle.json, so the creds couldn't live alongside the Dartmouth key. Centralizing
in credentials.load_kaggle_creds lets a single credentials.toml drive both.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from llmxive import credentials as C


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for k in ("KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_API_TOKEN"):
        monkeypatch.delenv(k, raising=False)


def _toml(tmp_path: Path, body: str, monkeypatch) -> None:
    p = tmp_path / "credentials.toml"
    p.write_text(body, encoding="utf-8")
    monkeypatch.setattr(
        C, "check_permissions",
        lambda: C.CredentialsCheck(ok=True, reason=None, path=p, exists=True),
    )


def test_env_pair_wins(monkeypatch):
    monkeypatch.setenv("KAGGLE_USERNAME", "u1")
    monkeypatch.setenv("KAGGLE_KEY", "k1")
    assert C.load_kaggle_creds() == ("u1", "k1")


def test_flat_keys_in_credentials_toml(tmp_path, monkeypatch):
    _toml(tmp_path, 'kaggle_username = "alice"\nkaggle_key = "abc"\n', monkeypatch)
    assert C.load_kaggle_creds() == ("alice", "abc")


def test_kaggle_table_in_credentials_toml(tmp_path, monkeypatch):
    _toml(tmp_path, '[kaggle]\nusername = "bob"\nkey = "xyz"\n', monkeypatch)
    assert C.load_kaggle_creds() == ("bob", "xyz")


def test_verbatim_token_in_credentials_toml(tmp_path, monkeypatch):
    _toml(tmp_path, 'kaggle_api_token = "{\\"username\\": \\"c\\", \\"key\\": \\"q\\"}"\n', monkeypatch)
    assert C.load_kaggle_creds() == ("c", "q")


def test_none_when_absent(tmp_path, monkeypatch):
    _toml(tmp_path, 'dartmouth_chat_api_key = "sk-x"\n', monkeypatch)
    monkeypatch.setattr(C.Path, "home", lambda: tmp_path / "nohome")
    assert C.load_kaggle_creds() is None
