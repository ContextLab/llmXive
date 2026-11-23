import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.verify_reproducibility import compute_file_sha256, verify_artifacts, generate_report

def test_compute_file_sha256():
    """Test that SHA256 computation is deterministic and correct."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = Path(f.name)
    
    try:
        hash1 = compute_file_sha256(temp_path)
        hash2 = compute_file_sha256(temp_path)
        
        assert hash1 == hash2
        # Known hash for "Hello, World!"
        expected = hashlib.sha256(b"Hello, World!").hexdigest()
        assert hash1 == expected
    finally:
        os.unlink(temp_path)

def test_verify_artifacts_success():
    """Test verification when all files match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create a file
        file_path = base / "data.txt"
        content = "Test content"
        file_path.write_text(content)
        
        expected_hash = compute_file_sha256(file_path)
        checksums = {
            "data.txt": expected_hash
        }
        
        results = verify_artifacts(checksums, base)
        
        assert results["verified"] == 1
        assert results["mismatched"] == 0
        assert results["missing"] == 0
        assert results["details"][0]["status"] == "verified"

def test_verify_artifacts_missing():
    """Test verification when a file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        checksums = {
            "missing_file.txt": "abc123"
        }
        
        results = verify_artifacts(checksums, base)
        
        assert results["verified"] == 0
        assert results["missing"] == 1
        assert results["details"][0]["status"] == "missing"

def test_verify_artifacts_mismatch():
    """Test verification when a file hash does not match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        # Create a file
        file_path = base / "data.txt"
        file_path.write_text("Real content")
        
        # Record a fake hash
        fake_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        checksums = {
            "data.txt": fake_hash
        }
        
        results = verify_artifacts(checksums, base)
        
        assert results["verified"] == 0
        assert results["mismatched"] == 1
        assert results["details"][0]["status"] == "mismatch"

def test_generate_report():
    """Test that the report is generated correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.json"
        
        results = {
            "verified": 1,
            "mismatched": 0,
            "missing": 0,
            "details": [{"path": "test.txt", "status": "verified", "hash": "abc"}]
        }
        
        generate_report(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path) as f:
            report = json.load(f)
        
        assert report["summary"]["verified"] == 1
        assert report["summary"]["reproducible"] is True
        assert "timestamp" in report
