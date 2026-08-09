"""
Unit tests for the downloaders.py checksum and state update logic.
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

from downloaders import (
    calculate_sha256,
    generate_checksum_file,
    update_state_file,
    DataFetchError
)

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"test content"
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        tmp_path.unlink()

def test_generate_checksum_file():
    """Test checksum file generation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        file_path = tmp_path / "test.txt"
        file_path.write_text("test data")
        
        checksum_dir = tmp_path / "checksums"
        checksum_dir.mkdir()
        
        result_path = generate_checksum_file(file_path, checksum_dir)
        
        assert result_path.exists()
        assert result_path.name == "test.txt.sha256"
        
        with open(result_path, 'r') as f:
            line = f.read().strip()
        
        parts = line.split()
        assert len(parts) == 2
        assert parts[1] == "test.txt"
        
        # Verify hash
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        assert parts[0] == expected_hash

def test_update_state_file_valid():
    """Test updating a valid state file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        state_file = tmp_path / "state.yaml"
        
        initial_state = {
            "artifact_hashes": {
                "existing.parquet": "abc123"
            }
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        update_state_file(state_file, "new.parquet", "def456")
        
        with open(state_file, 'r') as f:
            updated_state = yaml.safe_load(f)
        
        assert "artifact_hashes" in updated_state
        assert updated_state["artifact_hashes"]["existing.parquet"] == "abc123"
        assert updated_state["artifact_hashes"]["new.parquet"] == "def456"

def test_update_state_file_missing_key():
    """Test update_state_file raises ValueError if 'artifact_hashes' is missing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        state_file = tmp_path / "state.yaml"
        
        invalid_state = {
            "other_key": "value"
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(invalid_state, f)
        
        with pytest.raises(ValueError, match="missing the 'artifact_hashes' key"):
            update_state_file(state_file, "test.parquet", "hash123")

def test_update_state_file_not_dict():
    """Test update_state_file raises ValueError if 'artifact_hashes' is not a dict."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        state_file = tmp_path / "state.yaml"
        
        invalid_state = {
            "artifact_hashes": "not a dict"
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(invalid_state, f)
        
        with pytest.raises(ValueError, match="must be a dictionary"):
            update_state_file(state_file, "test.parquet", "hash123")

def test_calculate_sha256_file_not_found():
    """Test calculate_sha256 raises FileNotFoundError for missing file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        non_existent = Path(tmp_dir) / "non_existent.txt"
        
        with pytest.raises(FileNotFoundError):
            calculate_sha256(non_existent)
