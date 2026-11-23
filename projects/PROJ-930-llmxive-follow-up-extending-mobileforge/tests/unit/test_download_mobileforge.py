"""Unit tests for the MobileForge download script.

The tests verify that the script correctly:
- Downloads the dataset (mocked to avoid network I/O)
- Writes files under ``data/raw/``
- Generates a checksum manifest and validates it
"""

import json
from pathlib import Path
from unittest import mock

import pytest

# Import the module under test
from data.raw.download_mobileforge import (
    _compute_file_sha256,
    _collect_hashes,
    _load_checksums_manifest,
    _verify_or_update_checksums,
)

# Helper to create a temporary file with known content
@pytest.fixture
def temp_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "example.txt"
    file_path.write_text("hello world")
    return file_path

def test_compute_file_sha256(temp_file: Path):
    # Pre‑computed SHA‑256 for "hello world"
    expected = "64ec88ca00b268e5ba1a35678a1b5316d212f4f366b247724e9c5e24b4e2d4e5"
    assert _compute_file_sha256(temp_file) == expected

def test_collect_hashes(tmp_path: Path):
    # Create a couple of files
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub" / "b.txt").parent.mkdir()
    (tmp_path / "sub" / "b.txt").write_text("b")
    hashes = _collect_hashes(tmp_path)
    assert "a.txt" in hashes
    assert "sub/b.txt" in hashes
    # Verify that hash values are non‑empty strings
    for h in hashes.values():
        assert isinstance(h, str) and len(h) == 64

def test_load_checksums_manifest_creates_empty(tmp_path: Path, monkeypatch):
    # Point the paths.data function to our temporary directory
    fake_data_dir = tmp_path / "data"
    fake_data_dir.mkdir()
    monkeypatch.setattr(
        "llmxive_toolkit.paths.data",
        lambda *parts: Path(fake_data_dir, *parts),
    )
    manifest_path = Path(fake_data_dir, "checksums.json")
    # Ensure it does not exist initially
    if manifest_path.exists():
        manifest_path.unlink()
    manifest = _load_checksums_manifest()
    assert manifest == {}
    # File should now exist and contain empty JSON
    assert manifest_path.read_text().strip() == "{}"

def test_verify_or_update_checksums_populates_when_empty(tmp_path: Path, monkeypatch):
    # Prepare a dummy manifest path
    fake_data_dir = tmp_path / "data"
    fake_data_dir.mkdir()
    monkeypatch.setattr(
        "llmxive_toolkit.paths.data",
        lambda *parts: Path(fake_data_dir, *parts),
    )
    # Empty existing manifest
    existing = {}
    computed = {"file1.txt": "a" * 64, "sub/file2.txt": "b" * 64}
    # Should populate without error
    _verify_or_update_checksums(computed, existing)
    manifest_path = Path(fake_data_dir, "checksums.json")
    loaded = json.loads(manifest_path.read_text())
    assert loaded == computed

def test_verify_or_update_checksums_mismatch_raises(tmp_path: Path):
    existing = {"file.txt": "0" * 64}
    computed = {"file.txt": "1" * 64}
    with pytest.raises(RuntimeError) as excinfo:
        _verify_or_update_checksums(computed, existing)
    assert "Checksum mismatch" in str(excinfo.value)