import os
import json
import tempfile
import hashlib
import pytest
from unittest.mock import patch, MagicMock

# Mock config to avoid dependency on full project setup during unit tests
@pytest.fixture
def temp_config():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_raw = os.path.join(tmpdir, "data", "raw")
        os.makedirs(data_raw)
        
        # Create a test file
        test_file = os.path.join(data_raw, "test_file.csv")
        with open(test_file, "w") as f:
            f.write("id,smiles\n1,C\n")
        
        # Calculate hash
        with open(test_file, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Create checksums.json
        checksums_file = os.path.join(data_raw, "checksums.json")
        with open(checksums_file, "w") as f:
            json.dump({"test_file.csv": file_hash}, f)
        
        yield {
            "data_raw": data_raw,
            "test_file": test_file,
            "checksums_file": checksums_file,
            "expected_hash": file_hash
        }

def test_calculate_sha256(temp_config):
    """Test SHA-256 calculation function."""
    from code.utils.checksum_manager import calculate_sha256
    
    calculated = calculate_sha256(temp_config["test_file"])
    assert calculated == temp_config["expected_hash"]

def test_verify_checksum_success(temp_config):
    """Test successful checksum verification."""
    from code.utils.checksum_manager import load_checksums, verify_checksum_against_manifest
    
    checksums = load_checksums(temp_config["checksums_file"])
    assert "test_file.csv" in checksums
    assert checksums["test_file.csv"] == temp_config["expected_hash"]

def test_verify_checksum_missing_file(temp_config):
    """Test verification fails when file is missing."""
    from code.utils.checksum_manager import verify_checksum_against_manifest
    
    # Try to verify a file that doesn't exist
    non_existent = os.path.join(temp_config["data_raw"], "non_existent.csv")
    result = verify_checksum_against_manifest(non_existent, temp_config["checksums_file"])
    assert result is False

def test_verify_checksum_mismatch(temp_config):
    """Test verification fails when hash doesn't match."""
    from code.utils.checksum_manager import calculate_sha256, load_checksums
    
    # Create a file with wrong content
    wrong_file = os.path.join(temp_config["data_raw"], "wrong.csv")
    with open(wrong_file, "w") as f:
        f.write("wrong content")
    
    # Calculate its hash
    wrong_hash = calculate_sha256(wrong_file)
    
    # Update manifest with the wrong hash for this new file
    checksums = load_checksums(temp_config["checksums_file"])
    checksums["wrong.csv"] = "invalid_hash"
    with open(temp_config["checksums_file"], "w") as f:
        json.dump(checksums, f)
    
    # Verify should fail
    result = verify_checksum_against_manifest(wrong_file, temp_config["checksums_file"])
    assert result is False