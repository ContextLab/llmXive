"""
Unit tests for the hash_artifacts module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.hash_artifacts import (
    compute_file_hash,
    collect_files,
    hash_directory,
    load_state,
    save_state,
    update_state_with_hashes
)


def test_compute_file_hash(tmp_path):
    """Test SHA256 hash computation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)

    assert len(hash1) == 64  # SHA256 hex length
    assert hash1 == hash2  # Deterministic


def test_compute_file_hash_different_content(tmp_path):
    """Test that different content produces different hashes."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"

    file1.write_text("Content A")
    file2.write_text("Content B")

    hash1 = compute_file_hash(file1)
    hash2 = compute_file_hash(file2)

    assert hash1 != hash2


def test_collect_files(tmp_path):
    """Test file collection."""
    # Create test structure
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file1.txt").write_text("test")
    (tmp_path / "subdir" / "file2.txt").write_text("test")
    (tmp_path / "subdir" / "file3.py").write_text("test")

    # Collect all files
    all_files = collect_files(tmp_path)
    assert len(all_files) == 3

    # Collect only .txt files
    txt_files = collect_files(tmp_path, extensions=[".txt"])
    assert len(txt_files) == 2

    # Collect non-existent directory
    empty_files = collect_files(tmp_path / "nonexistent")
    assert len(empty_files) == 0


def test_hash_directory(tmp_path):
    """Test directory hashing."""
    # Create test structure
    (tmp_path / "subdir").mkdir()
    (tmp_path / "file1.txt").write_text("Content A")
    (tmp_path / "subdir" / "file2.txt").write_text("Content B")

    hashes = hash_directory(tmp_path)

    assert "file1.txt" in hashes
    assert "subdir/file2.txt" in hashes
    assert len(hashes) == 2


def test_load_state_nonexistent():
    """Test loading non-existent state file."""
    state = load_state(Path("nonexistent_state.json"))
    assert state == {}


def test_save_and_load_state(tmp_path):
    """Test saving and loading state."""
    state_path = tmp_path / "test_state.json"
    test_state = {
        "key1": "value1",
        "nested": {"key2": "value2"},
        "research_complete": True
    }

    save_state(state_path, test_state)

    loaded_state = load_state(state_path)
    assert loaded_state == test_state


def test_update_state_with_hashes(tmp_path):
    """Test updating state with directory hashes."""
    # Create test directory
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    (test_dir / "file1.txt").write_text("Content A")

    state = {}
    update_state_with_hashes(state, test_dir, "test_key")

    assert "test_key" in state
    assert "hashes" in state["test_key"]
    assert "timestamp" in state["test_key"]
    assert "file1.txt" in state["test_key"]["hashes"]


def test_update_state_with_nonexistent_directory(tmp_path, caplog):
    """Test updating state with non-existent directory."""
    state = {}
    update_state_with_hashes(state, tmp_path / "nonexistent", "test_key")

    assert "test_key" not in state