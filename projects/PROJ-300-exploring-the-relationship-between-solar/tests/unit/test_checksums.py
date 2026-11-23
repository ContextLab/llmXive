"""
Unit tests for checksum and state management functions.
"""
import os
import tempfile
import pytest
from pathlib import Path
import yaml
import json

from code.checksums import compute_sha256, scan_artifacts, generate_state_file, verify_checksums

def test_compute_sha256():
    """Test SHA256 computation on a known file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = compute_sha256(temp_path)
        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum)
    finally:
        os.unlink(temp_path)

def test_scan_artifacts():
    """Test artifact scanning function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file2 = Path(tmpdir) / "file2.json"
        file1.write_text("content1")
        file2.write_text('{"key": "value"}')
        
        artifacts = scan_artifacts(tmpdir, ["file1.txt", "file2.json"])
        
        assert len(artifacts) == 2
        paths = [a["path"] for a in artifacts]
        assert "file1.txt" in paths
        assert "file2.json" in paths
        
        # Check that each artifact has required fields
        for artifact in artifacts:
            assert "path" in artifact
            assert "checksum" in artifact
            assert "size_bytes" in artifact
            assert "mtime" in artifact

def test_generate_state_file():
    """Test state file generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        artifacts = [
            {"path": "data/test.csv", "checksum": "abc123", "size_bytes": 100, "mtime": "2023-01-01T00:00:00"},
            {"path": "results/test.json", "checksum": "def456", "size_bytes": 200, "mtime": "2023-01-02T00:00:00"}
        ]
        
        output_path = os.path.join(tmpdir, "state.yaml")
        generate_state_file(artifacts, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            state = yaml.safe_load(f)
        
        assert state["project"] == "PROJ-300-exploring-the-relationship-between-solar"
        assert "generated_at" in state
        assert state["task_id"] == "T041c"
        assert len(state["artifacts"]) == 2

def test_verify_checksums():
    """Test checksum verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files
        file1 = Path(tmpdir) / "file1.txt"
        file1.write_text("test content")
        
        # Create state file
        artifacts = [
            {
                "path": "file1.txt",
                "checksum": compute_sha256(str(file1)),
                "size_bytes": file1.stat().st_size,
                "mtime": "2023-01-01T00:00:00"
            }
        ]
        
        state_path = os.path.join(tmpdir, "state.yaml")
        generate_state_file(artifacts, state_path)
        
        # Verify should pass
        assert verify_checksums(state_path) is True
        
        # Modify file and verify should fail
        file1.write_text("modified content")
        assert verify_checksums(state_path) is False

def test_scan_artifacts_recursive():
    """Test recursive scanning of directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create nested directory structure
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        file1 = subdir / "file1.txt"
        file1.write_text("content")
        
        artifacts = scan_artifacts(tmpdir, ["subdir/*"])
        
        assert len(artifacts) == 1
        assert "subdir/file1.txt" in artifacts[0]["path"]