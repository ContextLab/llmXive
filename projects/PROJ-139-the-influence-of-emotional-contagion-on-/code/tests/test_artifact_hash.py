"""
Unit tests for artifact hashing functionality.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.utils.artifact_hash import (
    compute_file_hash,
    compute_directory_hash,
    hash_artifact,
    verify_artifact
)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def temp_dir():
    """Create a temporary directory with files."""
    temp_path = tempfile.mkdtemp()
    # Create files
    (Path(temp_path) / "file1.txt").write_text("Content 1")
    (Path(temp_path) / "file2.txt").write_text("Content 2")
    sub_dir = Path(temp_path) / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file3.txt").write_text("Content 3")
    yield temp_path
    # Cleanup
    import shutil
    shutil.rmtree(temp_path)

def test_compute_file_hash(temp_file):
    """Test file hashing produces consistent results."""
    hash1 = compute_file_hash(temp_file)
    hash2 = compute_file_hash(temp_file)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

def test_compute_file_hash_content_change(temp_file):
    """Test that changing file content changes hash."""
    original_hash = compute_file_hash(temp_file)
    Path(temp_file).write_text("Different content")
    new_hash = compute_file_hash(temp_file)
    assert original_hash != new_hash

def test_compute_directory_hash(temp_dir):
    """Test directory hashing produces consistent results."""
    hash1 = compute_directory_hash(temp_dir)
    hash2 = compute_directory_hash(temp_dir)
    assert hash1 == hash2
    assert len(hash1) == 64

def test_compute_directory_hash_file_count(temp_dir):
    """Test that directory hash includes correct file count."""
    hashes = compute_directory_hash(temp_dir)
    assert len(hashes) == 3  # file1, file2, file3

def test_hash_artifact_file():
    """Test hashing a single file and saving report."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Test content")
        temp_path = f.name
    
    report_path = temp_path + ".json"
    try:
        result_hash = hash_artifact(temp_path, report_path)
        assert len(result_hash) == 64
        
        # Verify report was saved
        assert os.path.exists(report_path)
        with open(report_path) as f:
            report = json.load(f)
        assert report["type"] == "file"
        assert report["hash"] == result_hash
    finally:
        os.unlink(temp_path)
        if os.path.exists(report_path):
            os.unlink(report_path)

def test_verify_artifact_success(temp_file):
    """Test successful artifact verification."""
    expected_hash = compute_file_hash(temp_file)
    assert verify_artifact(temp_file, expected_hash) is True

def test_verify_artifact_failure(temp_file):
    """Test failed artifact verification on mismatch."""
    wrong_hash = "a" * 64
    assert verify_artifact(temp_file, wrong_hash) is False

def test_verify_directory_artifact(temp_dir):
    """Test verification of directory artifact."""
    hashes = compute_directory_hash(temp_dir)
    combined_str = json.dumps(hashes, sort_keys=True)
    import hashlib
    expected_hash = hashlib.sha256(combined_str.encode()).hexdigest()
    assert verify_artifact(temp_dir, expected_hash) is True
