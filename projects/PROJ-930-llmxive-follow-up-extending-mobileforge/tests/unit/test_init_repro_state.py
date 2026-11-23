"""
Unit tests for ``code/init_repro_state.py``.

The tests verify that the bootstrap script creates the required JSON
files with the correct structure.
"""

import json
import os
from pathlib import Path

import pytest

from init_repro_state import _ensure_empty_checksums, _ensure_repro_meta, main
from llmxive_toolkit import paths

@pytest.fixture
def temp_data_dir(tmp_path: Path):
    """
    Temporarily redirect the ``paths.data`` and ``paths.outputs`` helpers to a
    temporary directory so the real project files are not polluted.
    """
    original_data = paths.data
    original_outputs = paths.outputs

    def temp_data(*parts):
        return tmp_path.joinpath(*parts)

    def temp_outputs(*parts):
        return tmp_path.joinpath(*parts)

    paths.data = temp_data  # type: ignore[assignment]
    paths.outputs = temp_outputs  # type: ignore[assignment]

    yield tmp_path

    paths.data = original_data  # type: ignore[assignment]
    paths.outputs = original_outputs  # type: ignore[assignment]

def test_ensure_empty_checksums_overwrites_existing(tmp_path: Path, monkeypatch):
    """Existing non‑empty checksums file should be overwritten with {}."""
    # Set up a non‑empty file
    checksum_path = tmp_path / "checksums.json"
    checksum_path.write_text('{"old_key":"old_val"}', encoding="utf-8")
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path.joinpath(*parts))
    _ensure_empty_checksums()
    assert checksum_path.is_file()
    with checksum_path.open() as f:
        content = json.load(f)
    assert content == {}

def test_ensure_repro_meta_creates_file_with_seed(tmp_path: Path, monkeypatch):
    """The meta file must be created and contain a non‑empty integer seed."""
    monkeypatch.setattr(paths, "outputs", lambda *parts: tmp_path.joinpath(*parts))
    # Ensure no env var interferes
    monkeypatch.delenv("RANDOM_SEED", raising=False)
    _ensure_repro_meta()
    meta_path = tmp_path / "reproducibility_meta.json"
    assert meta_path.is_file()
    with meta_path.open() as f:
        meta = json.load(f)
    assert isinstance(meta.get("seed"), int)
    assert "timestamp" in meta

def test_main_creates_both_artifacts(tmp_path: Path, monkeypatch):
    """Running ``main`` should create both required JSON files."""
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path.joinpath(*parts))
    monkeypatch.setattr(paths, "outputs", lambda *parts: tmp_path.joinpath(*parts))
    monkeypatch.delenv("RANDOM_SEED", raising=False)
    main()
    assert (tmp_path / "checksums.json").is_file()
    assert (tmp_path / "reproducibility_meta.json").is_file()