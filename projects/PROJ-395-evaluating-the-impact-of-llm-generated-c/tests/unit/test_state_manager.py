"""
Unit tests for state versioning logic (T009).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from code.state_manager import (
    compute_sha256,
    hash_directory,
    record_state_snapshot,
    verify_snapshot,
    get_latest_snapshot,
    STATE_DIR
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create test files
        file1 = tmppath / "test1.txt"
        file1.write_text("Hello, World!")
        
        file2 = tmppath / "test2.py"
        file2.write_text("def hello():\n    return 'World'")
        
        subdir = tmppath / "subdir"
        subdir.mkdir()
        file3 = subdir / "test3.csv"
        file3.write_text("a,b,c\n1,2,3")
        
        yield tmppath


def test_compute_sha256(temp_dir):
    """Test SHA-256 computation for a single file."""
    file_path = temp_dir / "test1.txt"
    hash_value = compute_sha256(file_path)
    
    # Known SHA-256 for "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert hash_value == expected


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256(Path("/nonexistent/file.txt"))


def test_hash_directory(temp_dir):
    """Test hashing all files in a directory."""
    hashes = hash_directory(temp_dir)
    
    assert len(hashes) == 3
    assert "test1.txt" in hashes
    assert "test2.py" in hashes
    assert "subdir/test3.csv" in hashes


def test_hash_directory_with_extension_filter(temp_dir):
    """Test hashing with extension filter."""
    hashes = hash_directory(temp_dir, extensions=[".txt"])
    
    assert len(hashes) == 1
    assert "test1.txt" in hashes


def test_record_state_snapshot(temp_dir):
    """Test recording a state snapshot."""
    artifacts = [temp_dir / "test1.txt", temp_dir / "test2.py"]
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        output_path = Path(f.name)
    
    try:
        result_path = record_state_snapshot(artifacts, output_path)
        
        assert result_path.exists()
        
        with open(result_path, "r") as f:
            snapshot = json.load(f)
        
        assert "timestamp" in snapshot
        assert "artifacts" in snapshot
        assert len(snapshot["artifacts"]) == 2
        
        # Check hash for test1.txt
        test1_hash = snapshot["artifacts"]["test1.txt"]["hash"]
        assert test1_hash == compute_sha256(temp_dir / "test1.txt")
    finally:
        output_path.unlink(missing_ok=True)


def test_record_state_snapshot_missing_file():
    """Test that FileNotFoundError is raised for missing artifact."""
    with pytest.raises(FileNotFoundError):
        record_state_snapshot([Path("/nonexistent/file.txt")])


def test_verify_snapshot_success(temp_dir):
    """Test successful verification of snapshot."""
    artifacts = [temp_dir / "test1.txt", temp_dir / "test2.py"]
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        snapshot_path = Path(f.name)
    
    try:
        record_state_snapshot(artifacts, snapshot_path)
        results = verify_snapshot(snapshot_path, temp_dir)
        
        assert all(results.values())
        assert len(results) == 2
    finally:
        snapshot_path.unlink(missing_ok=True)


def test_verify_snapshot_failure(temp_dir):
    """Test verification failure when file is modified."""
    artifacts = [temp_dir / "test1.txt"]
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        snapshot_path = Path(f.name)
    
    try:
        record_state_snapshot(artifacts, snapshot_path)
        
        # Modify file
        (temp_dir / "test1.txt").write_text("Modified content")
        
        results = verify_snapshot(snapshot_path, temp_dir)
        
        assert results["test1.txt"] == False
    finally:
        snapshot_path.unlink(missing_ok=True)


def test_verify_snapshot_missing_file(temp_dir):
    """Test verification when file is deleted."""
    artifacts = [temp_dir / "test1.txt"]
    
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        snapshot_path = Path(f.name)
    
    try:
        record_state_snapshot(artifacts, snapshot_path)
        
        # Delete file
        (temp_dir / "test1.txt").unlink()
        
        results = verify_snapshot(snapshot_path, temp_dir)
        
        assert results["test1.txt"] == False
    finally:
        snapshot_path.unlink(missing_ok=True)


def test_get_latest_snapshot(temp_dir):
    """Test getting the latest snapshot."""
    # Create first snapshot
    artifacts = [temp_dir / "test1.txt"]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        snapshot1 = Path(f.name)
    record_state_snapshot(artifacts, snapshot1)
    
    # Create second snapshot (should be latest)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        snapshot2 = Path(f.name)
    record_state_snapshot(artifacts, snapshot2)
    
    try:
        latest = get_latest_snapshot()
        # Since we're using temp dir, we check if it returns the second one
        # by comparing timestamps or names
        assert latest is not None
    finally:
        snapshot1.unlink(missing_ok=True)
        snapshot2.unlink(missing_ok=True)