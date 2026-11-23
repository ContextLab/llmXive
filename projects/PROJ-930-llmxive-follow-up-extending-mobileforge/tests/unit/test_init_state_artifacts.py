"""
Unit tests for ``code/init_state_artifacts.py``.

These tests verify that the initialisation script creates the required JSON
files under the ``data/`` directory and that they contain an empty JSON
object.
"""

import json
from pathlib import Path

import pytest

# Import the module under test
from init_state_artifacts import (
    ensure_artifact_hashes,
    ensure_checksums_manifest,
    _write_empty_json,
)
from llmxive_toolkit import paths

@pytest.fixture
def temp_data_dir(tmp_path: Path):
    """
    Replace the default ``paths.data`` root with a temporary directory for
    the duration of a test. This avoids polluting the real project data
    folder.
    """
    original_root = paths.root
    # Monkey‑patch the ``paths.data`` function to point inside ``tmp_path``
    def temp_data(*parts):
        return tmp_path.joinpath(*parts)

    # Store original reference and replace
    original_data = paths.data
    paths.data = temp_data  # type: ignore[assignment]

    yield tmp_path

    # Restore original function after test
    paths.data = original_data  # type: ignore[assignment]

def test_write_empty_json_overwrites_invalid_content(tmp_path: Path):
    """If a file exists but does not contain a dict, it should be overwritten."""
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("[]", encoding="utf-8")  # write a JSON list
    _write_empty_json(bad_path)
    with bad_path.open() as f:
        data = json.load(f)
    assert data == {}

def test_write_empty_json_preserves_valid_dict(tmp_path: Path):
    """If a file already contains a dict, the function should leave it untouched."""
    good_path = tmp_path / "good.json"
    good_path.write_text(json.dumps({"already": "present"}), encoding="utf-8")
    _write_empty_json(good_path)
    with good_path.open() as f:
        data = json.load(f)
    assert data == {"already": "present"}

def test_ensure_artifact_hashes_creates_file(temp_data_dir: Path):
    """ensure_artifact_hashes must create data/artifact_hashes.json with {}."""
    ensure_artifact_hashes()
    manifest_path = paths.data("artifact_hashes.json")
    assert manifest_path.is_file()
    with manifest_path.open() as f:
        content = json.load(f)
    assert content == {}

def test_ensure_checksums_manifest_creates_file(temp_data_dir: Path):
    """ensure_checksums_manifest must create data/checksums.json with {}."""
    ensure_checksums_manifest()
    manifest_path = paths.data("checksums.json")
    assert manifest_path.is_file()
    with manifest_path.open() as f:
        content = json.load(f)
    assert content == {}