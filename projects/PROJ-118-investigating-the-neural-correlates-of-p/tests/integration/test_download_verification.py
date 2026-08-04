import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import hashlib

# Import the functions we are testing
# We assume the code is in code/download.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from download import calculate_sha256, verify_checksum, get_manifest_hash

def test_calculate_sha256():
    """Test that SHA256 calculation is deterministic and correct."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"Hello, World!")
        temp_path = Path(f.name)
    
    try:
        # "Hello, World!" SHA256 is known
        expected = "d9014c4624844aa5bac314773d6b689ad467fa4e1d1a50a1b8a99d5a95f72ff5"
        actual = calculate_sha256(temp_path)
        assert actual == expected, f"Expected {expected}, got {actual}"
    finally:
        os.unlink(temp_path)

def test_verify_checksum_success():
    """Test that verification passes when hashes match."""
    content = b"Test content for verification"
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        hash_val = calculate_sha256(temp_path)
        # This should not raise
        verify_checksum(temp_path, hash_val)
    finally:
        os.unlink(temp_path)

def test_verify_checksum_failure():
    """Test that verification raises ValueError when hashes do not match."""
    content = b"Test content"
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError) as exc_info:
            verify_checksum(temp_path, "invalid_hash_string")
        assert "Checksum verification FAILED" in str(exc_info.value)
    finally:
        os.unlink(temp_path)

def test_get_manifest_hash():
    """Test parsing a mock manifest file."""
    mock_manifest = [
        {"filename": "sub-01_eeg.json", "checksum": "abc123"},
        {"filename": "sub-02_eeg.json", "checksum": "def456"}
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(mock_manifest, f)
        manifest_path = Path(f.name)
    
    try:
        # Test finding a known key
        result = get_manifest_hash("ds003645", "sub-01_eeg.json", manifest_path)
        assert result == "abc123"
        
        # Test missing key
        result_missing = get_manifest_hash("ds003645", "missing.json", manifest_path)
        assert result_missing is None
    finally:
        os.unlink(manifest_path)

def test_full_verification_flow():
    """
    Integration test simulating the T011 workflow:
    1. Create a mock manifest and data files.
    2. Run verification.
    3. Ensure it passes for correct files and fails for incorrect ones.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create mock data files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("content2")
        
        # Create manifest
        h1 = calculate_sha256(file1)
        h2 = calculate_sha256(file2)
        
        manifest_data = [
            {"filename": "file1.txt", "checksum": h1},
            {"filename": "file2.txt", "checksum": h2}
        ]
        
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f)
        
        # Test successful verification
        # We need to adapt the run_download_pipeline logic to use our mock manifest
        # Since run_download_pipeline expects a specific text format for checksums.txt
        # Let's test the core verification logic directly here as a proxy for the pipeline
        
        for f_path, expected_h in [(file1, h1), (file2, h2)]:
            verify_checksum(f_path, expected_h)
        
        # Test failure
        file3 = tmp_path / "file3.txt"
        file3.write_text("wrong content")
        with pytest.raises(ValueError):
            verify_checksum(file3, h1)
