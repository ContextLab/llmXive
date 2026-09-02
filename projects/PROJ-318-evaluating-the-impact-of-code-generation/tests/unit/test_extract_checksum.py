"""
Unit tests for T019: Checksum computation and state recording.
"""
import json
import hashlib
import tempfile
import os
from pathlib import Path
import yaml
import pytest

# Import functions to test
from extract import compute_file_checksum, record_state_hash

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_checksum(temp_dir):
    """Test SHA-256 checksum computation."""
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    checksum = compute_file_checksum(test_file)
    
    # Verify checksum matches expected SHA-256
    expected = hashlib.sha256(content).hexdigest()
    assert checksum == expected
    assert len(checksum) == 64  # SHA-256 hex string length

def test_compute_file_checksum_large_file(temp_dir):
    """Test checksum with larger file."""
    test_file = temp_dir / "large.txt"
    content = b"X" * 1000000  # 1MB
    test_file.write_bytes(content)
    
    checksum = compute_file_checksum(test_file)
    expected = hashlib.sha256(content).hexdigest()
    assert checksum == expected

def test_record_state_hash_creates_file(temp_dir):
    """Test that record_state_hash creates the state file."""
    # Create a test file
    test_file = temp_dir / "test.json"
    test_file.write_text(json.dumps({"key": "value"}))
    
    state_file = temp_dir / "state.yaml"
    
    record_state_hash([test_file], state_file)
    
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        state_data = yaml.safe_load(f)
    
    assert 'artifact_hashes' in state_data
    assert 'test.json' in state_data['artifact_hashes']
    assert len(state_data['artifact_hashes']['test.json']) == 64

def test_record_state_hash_updates_existing(temp_dir):
    """Test that record_state_hash updates existing state."""
    state_file = temp_dir / "state.yaml"
    
    # Create initial state
    initial_data = {
        'artifact_hashes': {
            'existing.json': 'abc123'
        }
    }
    with open(state_file, 'w') as f:
        yaml.dump(initial_data, f)
    
    # Add new file
    test_file = temp_dir / "new.json"
    test_file.write_text(json.dumps({"new": "data"}))
    
    record_state_hash([test_file], state_file)
    
    with open(state_file, 'r') as f:
        state_data = yaml.safe_load(f)
    
    assert 'existing.json' in state_data['artifact_hashes']
    assert state_data['artifact_hashes']['existing.json'] == 'abc123'
    assert 'new.json' in state_data['artifact_hashes']
    assert len(state_data['artifact_hashes']['new.json']) == 64

def test_record_state_hash_creates_directory(temp_dir):
    """Test that record_state_hash creates parent directories."""
    state_file = temp_dir / "deep" / "nested" / "state.yaml"
    
    test_file = temp_dir / "test.json"
    test_file.write_text(json.dumps({"key": "value"}))
    
    record_state_hash([test_file], state_file)
    
    assert state_file.exists()
    assert state_file.parent.exists()
