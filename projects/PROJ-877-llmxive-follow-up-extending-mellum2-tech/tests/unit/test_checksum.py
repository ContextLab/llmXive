"""
Unit tests for code/data/checksum.py
"""
import pytest
import os
import json
from pathlib import Path
from data.checksum import (
    compute_sha256,
    compute_directory_checksums,
    save_checksums,
    load_checksums,
    verify_checksums,
    ensure_data_directories
)

def test_compute_sha256_file(tmp_path):
    """Verify SHA256 computation on a file."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_sha256(test_file)
    
    assert checksum is not None
    assert len(checksum) == 64  # SHA256 hex length

def test_compute_directory_checksums(tmp_path):
    """Verify directory checksum computation."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")
    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")
    
    checksums = compute_directory_checksums(tmp_path)
    
    assert len(checksums) == 2
    assert "file1.txt" in checksums
    assert "file2.txt" in checksums

def test_save_and_load_checksums(tmp_path):
    """Verify saving and loading checksums."""
    checksums = {
        "file1.txt": "abc123",
        "file2.txt": "def456"
    }
    save_path = tmp_path / "checksums.json"
    
    save_checksums(checksums, save_path)
    assert save_path.exists()
    
    loaded = load_checksums(save_path)
    assert loaded == checksums

def test_verify_checksums_success(tmp_path):
    """Verify checksum verification when files are intact."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")
    
    original_checksum = compute_sha256(file1)
    checksums = {"file1.txt": original_checksum}
    
    is_valid = verify_checksums(checksums, tmp_path)
    assert is_valid is True

def test_verify_checksums_failure(tmp_path):
    """Verify checksum verification detects modification."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")
    
    # Record original
    original_checksum = compute_sha256(file1)
    checksums = {"file1.txt": original_checksum}
    
    # Modify file
    file1.write_text("Modified Content")
    
    is_valid = verify_checksums(checksums, tmp_path)
    assert is_valid is False

def test_ensure_data_directories_creates_structure(tmp_path):
    """Verify ensure_data_directories creates the expected structure."""
    data_dir = tmp_path / "data"
    ensure_data_directories(data_dir)
    
    assert (data_dir / "raw").exists()
    assert (data_dir / "processed").exists()
    assert (data_dir / "results").exists()
