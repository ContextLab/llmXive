"""
Unit tests for state_manager module.
"""
import os
import tempfile
import yaml
import pytest
from pathlib import Path

# Import the module functions
from code.state_manager import (
    calculate_file_checksum,
    scan_raw_data_directory,
    generate_state_checksums,
    write_state_file,
    verify_state_checksums
)

def test_calculate_file_checksum():
    """Test checksum calculation for a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = calculate_file_checksum(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)
    finally:
        os.unlink(temp_path)

def test_generate_state_checksums():
    """Test checksum generation for a list of files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("data")
        
        # Generate checksums
        checksums = generate_state_checksums([test_file])
        
        assert test_file in checksums
        assert checksums[test_file]["status"] == "verified"
        assert checksums[test_file]["checksum"] is not None

def test_write_and_verify_state_file():
    """Test writing and verifying a state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file
        test_file = os.path.join(tmpdir, "data.txt")
        with open(test_file, "w") as f:
            f.write("original content")
        
        # Generate and write checksums
        checksums = generate_state_checksums([test_file])
        state_path = os.path.join(tmpdir, "state.yaml")
        write_state_file(checksums, state_path)
        
        # Verify integrity
        assert verify_state_checksums(state_path) is True
        
        # Modify file and verify failure
        with open(test_file, "w") as f:
            f.write("modified content")
        
        assert verify_state_checksums(state_path) is False
