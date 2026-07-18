"""
Tests for the Reproducibility Verification Script (T028)
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import yaml

from code.data.verify_reproducibility import (
    compute_file_sha256,
    load_recorded_checksums,
    verify_artifacts,
    generate_report
)

def test_compute_file_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        # "test content" sha256
        expected = hashlib.sha256(b"test content").hexdigest()
        result = compute_file_sha256(temp_path)
        assert result == expected
    finally:
        os.unlink(temp_path)

def test_compute_file_sha256_missing():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_file_sha256(Path("/nonexistent/file.txt"))

def test_load_recorded_checksums_missing_file():
    """Test loading from non-existent state file."""
    with patch('code.data.verify_reproducibility.get_config') as mock_config:
        mock_config.return_value.project_state_file = "/nonexistent/state.yaml"
        with pytest.raises(FileNotFoundError):
            load_recorded_checksums(mock_config.return_value)

def test_load_recorded_checksums_success():
    """Test loading checksums from a valid YAML file."""
    checksums_data = {
        "artifact_checksums": {
            "data/processed/test.csv": "abc123",
            "data/processed/results.json": "def456"
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(checksums_data, f)
        temp_path = f.name
    
    try:
        mock_config = MagicMock()
        mock_config.project_state_file = temp_path
        
        result = load_recorded_checksums(mock_config)
        assert result == checksums_data["artifact_checksums"]
    finally:
        os.unlink(temp_path)

def test_verify_artifacts_matches():
    """Test verification where all files match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create a file
        test_file = base / "test.txt"
        test_file.write_text("content")
        hash_val = compute_file_sha256(test_file)
        
        recorded = {"test.txt": hash_val}
        
        matches, mismatches, missing = verify_artifacts(recorded, base)
        
        assert "test.txt" in matches
        assert len(mismatches) == 0
        assert len(missing) == 0

def test_verify_artifacts_mismatch():
    """Test verification where a file has changed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create a file
        test_file = base / "test.txt"
        test_file.write_text("content")
        old_hash = "wrong_hash_123"
        
        recorded = {"test.txt": old_hash}
        
        matches, mismatches, missing = verify_artifacts(recorded, base)
        
        assert "test.txt" not in matches
        assert "test.txt" in mismatches
        assert len(missing) == 0

def test_verify_artifacts_missing():
    """Test verification where a file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        recorded = {"missing.txt": "some_hash"}
        
        matches, mismatches, missing = verify_artifacts(recorded, base)
        
        assert len(matches) == 0
        assert len(mismatches) == 0
        assert "missing.txt" in missing

def test_generate_report_success():
    """Test report generation for successful verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.json"
        
        matches = {"file1.txt": "hash1"}
        mismatches = {}
        missing = []
        
        report = generate_report(matches, mismatches, missing, output_path)
        
        assert report["status"] == "success"
        assert report["verified_count"] == 1
        assert report["mismatch_count"] == 0
        assert os.path.exists(output_path)
        
        with open(output_path) as f:
            saved = json.load(f)
        assert saved["status"] == "success"

def test_generate_report_failure():
    """Test report generation for failed verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.json"
        
        matches = {}
        mismatches = {"file1.txt": ("old", "new")}
        missing = ["file2.txt"]
        
        report = generate_report(matches, mismatches, missing, output_path)
        
        assert report["status"] == "failed"
        assert report["mismatch_count"] == 1
        assert report["missing_count"] == 1