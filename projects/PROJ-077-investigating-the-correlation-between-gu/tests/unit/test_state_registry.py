"""
Unit tests for the state_registry module.
"""
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from state_registry import (
    calculate_file_checksum, 
    scan_raw_data_directory, 
    initialize_state_registry, 
    load_state_registry,
    verify_file_checksums
)
from logging_config import get_logger

logger = get_logger(__name__)

def test_calculate_file_checksum():
    """Test that checksum calculation is deterministic and correct."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_file_checksum(temp_path)
        assert isinstance(checksum, str)
        assert len(checksum) == 64 # SHA256 hex length
        
        # Verify determinism
        checksum2 = calculate_file_checksum(temp_path)
        assert checksum == checksum2
    finally:
        os.unlink(temp_path)

def test_scan_raw_data_directory():
    """Test scanning a directory for files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create nested structure
        (tmp_path / "subdir").mkdir()
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "subdir" / "file2.txt"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        result = scan_raw_data_directory(tmp_path)
        
        assert len(result) == 2
        assert "file1.txt" in result
        assert "subdir/file2.txt" in result or "subdir\\file2.txt" in result

def test_initialize_and_load_state_registry():
    """Test creating and loading a state registry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        raw_path = Path(tmpdir) / "raw"
        raw_path.mkdir()
        
        # Create a dummy file
        dummy_file = raw_path / "data.csv"
        dummy_file.write_text("col1,col2\n1,2")
        
        initialize_state_registry(state_path, raw_path)
        
        assert state_path.exists()
        
        registry = load_state_registry(state_path)
        assert registry is not None
        assert "artifact_hashes" in registry
        assert len(registry["artifact_hashes"]) == 1

def test_verify_file_checksums():
    """Test verifying checksums for multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        file1 = tmp_path / "f1.txt"
        file2 = tmp_path / "f2.txt"
        
        file1.write_text("a")
        file2.write_text("b")
        
        result = verify_file_checksums([file1, file2])
        
        assert len(result) == 2
        assert str(file1) in result
        assert str(file2) in result