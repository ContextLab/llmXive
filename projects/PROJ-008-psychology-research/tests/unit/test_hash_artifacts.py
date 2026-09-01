"""
Unit tests for the artifact hashing utility (T008).

These tests verify the correctness of the hashing logic, exclusion patterns,
and manifest generation without requiring actual large file systems.
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from scripts.hash_artifacts import (
    compute_file_hash,
    should_exclude,
    hash_artifacts,
    save_manifest,
    EXCLUDE_PATTERNS
)

def test_compute_file_hash():
    """Test that compute_file_hash returns correct SHA-256 hash."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)

    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        actual_hash = compute_file_hash(temp_path)
        assert actual_hash == expected_hash, f"Expected {expected_hash}, got {actual_hash}"
    finally:
        temp_path.unlink()

def test_compute_file_hash_nonexistent():
    """Test that compute_file_hash returns None for non-existent files."""
    result = compute_file_hash(Path("/nonexistent/file.txt"))
    assert result is None

def test_should_exclude_hidden_files():
    """Test that hidden files are excluded."""
    assert should_exclude(Path(".gitignore")) is True
    assert should_exclude(Path("data/.DS_Store")) is True

def test_should_exclude_log_files():
    """Test that log files are excluded."""
    assert should_exclude(Path("output.log")) is True
    assert should_exclude(Path("data/raw/retrieval.log")) is True

def test_should_exclude_manifest():
    """Test that the manifest file itself is excluded."""
    assert should_exclude(Path("data/processed/artifact_manifest.json")) is True

def test_should_exclude_pycache():
    """Test that __pycache__ directories are excluded."""
    assert should_exclude(Path("__pycache__/module.cpython-311.pyc")) is True

def test_should_exclude_normal_file():
    """Test that normal files are not excluded."""
    assert should_exclude(Path("data/processed/cleaned_studies.csv")) is False
    assert should_exclude(Path("code/analysis/meta_analysis.py")) is False

def test_save_manifest_creates_directory():
    """Test that save_manifest creates the directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "subdir" / "manifest.json"
        artifacts = [{"path": "test.txt", "hash": "abc123", "size_bytes": 10}]
        
        result = save_manifest(artifacts, manifest_path)
        
        assert result is True
        assert manifest_path.exists()
        
        with open(manifest_path, 'r') as f:
            data = json.load(f)
            assert len(data["artifacts"]) == 1
            assert data["artifacts"][0]["path"] == "test.txt"

def test_hash_artifacts_empty_directory():
    """Test hashing an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create an empty directory structure
        test_dir = Path(tmpdir) / "test_dir"
        test_dir.mkdir()
        
        artifacts = hash_artifacts(["test_dir"], Path(tmpdir))
        assert len(artifacts) == 0

def test_hash_artifacts_with_files():
    """Test hashing a directory with files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_dir"
        test_dir.mkdir()
        
        # Create a test file
        test_file = test_dir / "test.txt"
        test_file.write_text("Test content")
        
        artifacts = hash_artifacts(["test_dir"], Path(tmpdir))
        
        assert len(artifacts) == 1
        assert artifacts[0]["path"] == "test_dir/test.txt"
        assert "hash" in artifacts[0]
        assert artifacts[0]["size_bytes"] == len("Test content")