"""Unit tests for src.data.download (no network access required)."""

import json
from pathlib import Path

import pytest

from src.data.download import (
    _load_expected_hashes,
    _sha256,
    _snippet_id,
    _write_excluded,
)


def test_sha256_matches_known_value(tmp_path: Path):
  target = tmp_path / "f.bin"
  target.write_bytes(b"hello")
  # sha256("hello")
  assert (
      _sha256(target)
      == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
  )


def test_write_excluded_creates_json_array(tmp_path: Path):
  out = tmp_path / "excluded.json"
  records = [
      {"snippet_id": "a", "code": "x=1", "human_comment": "", "reason": "invalid_docstring"}
  ]
  _write_excluded(records, out)
  data = json.loads(out.read_text())
  assert isinstance(data, list)
  assert data[0]["reason"] == "invalid_docstring"


def test_load_expected_handles_bootstrap_manifest(tmp_path: Path, monkeypatch):
  manifest = tmp_path / "artifact_hashes.yaml"
  manifest.write_text("# bootstrap\n{}\n")
  monkeypatch.setattr(
      "src.data.download.paths.data", lambda *a: tmp_path / a[-1]
  )
  assert _load_expected_hashes() == {}


def test_load_expected_missing_manifest_raises(tmp_path: Path, monkeypatch):
  monkeypatch.setattr(
      "src.data.download.paths.data", lambda *a: tmp_path / a[-1]
  )
  with pytest.raises(FileNotFoundError):
      _load_expected_hashes()


def test_snippet_id_is_deterministic():
  a = _snippet_id("train", 3)
  b = _snippet_id("train", 3)
  c = _snippet_id("train", 4)
  assert a == b
  assert a != c