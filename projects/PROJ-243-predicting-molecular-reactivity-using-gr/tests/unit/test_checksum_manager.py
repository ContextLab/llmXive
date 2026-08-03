import os
import json
import tempfile
import pytest
from code.utils.checksum_manager import (
    calculate_sha256,
    load_checksums,
    save_checksums,
    update_checksum_for_file,
    verify_checksum_against_manifest,
    initialize_checksums_template
)

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        # Known hash for "test content"
        expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        actual_hash = calculate_sha256(temp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(temp_path)

def test_load_and_save_checksums():
    """Test loading and saving checksums JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksums_path = os.path.join(tmpdir, "checksums.json")
        test_data = {
            "test_key": {
                "hash": "abc123",
                "source_url": "http://example.com"
            }
        }
        
        save_checksums(checksums_path, test_data)
        loaded_data = load_checksums(checksums_path)
        
        assert loaded_data == test_data

def test_update_checksum_for_file():
    """Test updating the checksum manifest with a real file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        file_path = os.path.join(tmpdir, "test.txt")
        with open(file_path, "w") as f:
            f.write("test data")
        
        checksums_path = os.path.join(tmpdir, "checksums.json")
        
        # Update the manifest
        update_checksum_for_file(
            checksums_path,
            "test_file",
            file_path,
            source_url="local:test",
            version="1.0"
        )
        
        # Verify the update
        checksums = load_checksums(checksums_path)
        assert "test_file" in checksums
        assert checksums["test_file"]["source_url"] == "local:test"
        assert len(checksums["test_file"]["hash"]) == 64  # SHA-256 hex length

def test_verify_checksum_success():
    """Test successful checksum verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        file_path = os.path.join(tmpdir, "test.txt")
        with open(file_path, "w") as f:
            f.write("verify me")
        
        checksums_path = os.path.join(tmpdir, "checksums.json")
        
        # First, update the manifest with the correct hash
        update_checksum_for_file(checksums_path, "test", file_path)
        
        # Then verify
        assert verify_checksum_against_manifest(checksums_path, "test", file_path) is True

def test_verify_checksum_failure():
    """Test failed checksum verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        file_path = os.path.join(tmpdir, "test.txt")
        with open(file_path, "w") as f:
            f.write("original content")
        
        checksums_path = os.path.join(tmpdir, "checksums.json")
        
        # Update manifest with a WRONG hash
        update_checksum_for_file(checksums_path, "test", file_path)
        
        # Modify the file content
        with open(file_path, "w") as f:
            f.write("modified content")
        
        # Verify should fail
        assert verify_checksum_against_manifest(checksums_path, "test", file_path) is False

def test_initialize_checksums_template():
    """Test creating the initial checksums template."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checksums_path = os.path.join(tmpdir, "checksums.json")
        
        initialize_checksums_template(checksums_path)
        
        assert os.path.exists(checksums_path)
        data = load_checksums(checksums_path)
        
        assert "reference_substructures" in data
        assert "kinetic_dataset" in data
        assert data["reference_substructures"]["hash"] == ""
        assert data["kinetic_dataset"]["hash"] == ""