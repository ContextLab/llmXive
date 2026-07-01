"""
Tests for utils.py functions.
"""
import os
import tempfile
import pytest
from pathlib import Path
from utils import generate_checksum, update_state_file, validate_file_exists
import yaml

def test_generate_checksum():
    """Test SHA256 generation for a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name

    try:
        checksum = generate_checksum(temp_path)
        # Known SHA256 for "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_validate_file_exists():
    """Test file existence validation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        temp_path = f.name
    
    try:
        assert validate_file_exists(temp_path) is True
        assert validate_file_exists("/nonexistent/file.txt") is False
    finally:
        os.unlink(temp_path)

def test_update_state_file():
    """Test state file update logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, "test_state.yaml")
        
        # Initial update
        update_state_file({"file1.txt": "hash1"}, state_path)
        
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['artifact_hashes']['file1.txt'] == 'hash1'
        assert 'last_updated' in data
        
        # Update with new hash
        update_state_file({"file1.txt": "hash2", "file2.txt": "hash3"}, state_path)
        
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['artifact_hashes']['file1.txt'] == 'hash2'
        assert data['artifact_hashes']['file2.txt'] == 'hash3'