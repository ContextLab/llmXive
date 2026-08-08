import os
import tempfile
from pathlib import Path
import pytest
import hashlib
from unittest.mock import patch, MagicMock

# Import the functions to test
from downloaders import calculate_sha256, generate_checksum_file, update_state_file

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test data")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_sha256(temp_path)
        expected = hashlib.sha256(b"test data").hexdigest()
        assert checksum == expected
    finally:
        os.unlink(temp_path)

def test_generate_checksum_file():
    """Test checksum file generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_file = tmpdir_path / "test.parquet"
        test_file.write_text("test data")
        
        checksum_file = generate_checksum_file(test_file)
        
        assert checksum_file.exists()
        assert checksum_file.suffix == ".sha256"
        
        with open(checksum_file, 'r') as f:
            content = f.read()
        
        # Check format: <hash>  <filename>
        parts = content.strip().split()
        assert len(parts) == 2
        assert parts[1] == "test.parquet"
        
        # Verify hash is correct
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        assert parts[0] == expected_hash

def test_update_state_file():
    """Test state file update."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        state_file = tmpdir_path / "state.yaml"
        
        # Mock the PROJECT_STATE_FILE and STATE_DIR
        with patch('downloaders.PROJECT_STATE_FILE', state_file), \
             patch('downloaders.STATE_DIR', tmpdir_path):
            
            checksums = {
                'oqmd.parquet': 'abc123',
                'aflow.parquet': 'def456'
            }
            
            update_state_file(checksums)
            
            assert state_file.exists()
            content = state_file.read_text()
            assert 'artifact_hashes' in content
            assert 'oqmd.parquet' in content
            assert 'abc123' in content
            assert 'aflow.parquet' in content
            assert 'def456' in content
