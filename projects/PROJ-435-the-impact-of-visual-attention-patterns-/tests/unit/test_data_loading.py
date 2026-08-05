"""
Unit tests for code/utils/data_loading.py
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.data_loading import (
    compute_sha256,
    load_hash_registry,
    save_hash_registry,
    verify_checksum,
    parse_research_md
)
from code.utils.data_loading import STATE_DIR, PROJECT_ROOT

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    # Create a temp file
    test_file = PROJECT_ROOT / "temp_test_sha.txt"
    content = b"test content for hashing"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_sha256(test_file)
    
    assert actual_hash == expected_hash
    test_file.unlink()

def test_load_hash_registry_empty():
    """Test loading registry when file doesn't exist."""
    # Ensure file doesn't exist
    hash_file = STATE_DIR / "data_hashes.json"
    if hash_file.exists():
        hash_file.unlink()
    
    registry = load_hash_registry()
    assert registry == {}

def test_save_and_load_hash_registry():
    """Test saving and loading registry."""
    test_registry = {"file1.parquet": "abc123", "file2.parquet": "def456"}
    save_hash_registry(test_registry)
    
    loaded_registry = load_hash_registry()
    assert loaded_registry == test_registry

def test_verify_checksum_new_file():
    """Test verification of a new file."""
    # Create a temp file
    test_file = PROJECT_ROOT / "temp_verify_test.parquet"
    content = b"new file content"
    test_file.write_bytes(content)
    
    hash_file = STATE_DIR / "data_hashes.json"
    if hash_file.exists():
        hash_file.unlink() # Start fresh
    
    registry = load_hash_registry()
    # Should not raise
    verify_checksum(test_file, "temp_verify_test.parquet", registry)
    
    # Check registry was updated
    assert "temp_verify_test.parquet" in registry
    
    test_file.unlink()

def test_verify_checksum_mismatch():
    """Test verification fails on mismatch."""
    # Create a temp file
    test_file = PROJECT_ROOT / "temp_mismatch.parquet"
    content = b"mismatch content"
    test_file.write_bytes(content)
    
    # Pre-populate registry with wrong hash
    registry = {"temp_mismatch.parquet": "wrong_hash_12345"}
    
    with pytest.raises(ValueError, match="Checksum mismatch"):
        verify_checksum(test_file, "temp_mismatch.parquet", registry)
    
    test_file.unlink()

@patch('code.utils.data_loading.RESEARCH_MD_PATH')
def test_parse_research_md(mock_path):
    """Test parsing URL from research.md."""
    mock_content = """
    Some text...
    VERIFIED REAL DATA SOURCE
    https://example.com/dataset/eye_tracking_v1.parquet
    More text...
    """
    mock_path.read_text.return_value = mock_content
    mock_path.exists.return_value = True
    
    url = parse_research_md()
    assert url == "https://example.com/dataset/eye_tracking_v1.parquet"

@patch('code.utils.data_loading.RESEARCH_MD_PATH')
def test_parse_research_md_missing_block(mock_path):
    """Test error when block is missing."""
    mock_path.read_text.return_value = "No verified source here"
    mock_path.exists.return_value = True
    
    with pytest.raises(ValueError, match="Could not find"):
        parse_research_md()