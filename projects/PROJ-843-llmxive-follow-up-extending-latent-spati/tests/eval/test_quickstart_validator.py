"""
Unit tests for T024 Quickstart Validator.
These tests verify the validator's logic without running the full pipeline.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import json
import numpy as np

# Add code to path
if 'code' in str(Path(__file__).parent):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from eval.quickstart_validator import (
    validate_file_exists,
    validate_directory,
    log_status
)


def test_validate_file_exists_found():
    """Test that validate_file_exists returns True for existing non-empty file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        f.flush()
        path = Path(f.name)
    
    try:
        result = validate_file_exists(path, "Test File")
        assert result is True
    finally:
        os.unlink(path)


def test_validate_file_exists_missing():
    """Test that validate_file_exists returns False for missing file."""
    path = Path("/tmp/this_file_does_not_exist_12345.npy")
    result = validate_file_exists(path, "Missing File")
    assert result is False


def test_validate_file_exists_empty():
    """Test that validate_file_exists returns False for empty file."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"")
        f.flush()
        path = Path(f.name)
    
    try:
        result = validate_file_exists(path, "Empty File")
        assert result is False
    finally:
        os.unlink(path)


def test_validate_directory_ok():
    """Test validate_directory with sufficient files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create 5 files
        for i in range(5):
            (Path(tmpdir) / f"file_{i}.txt").write_text("data")
        
        result = validate_directory(Path(tmpdir), "Test Dir", min_files=3)
        assert result is True


def test_validate_directory_too_few():
    """Test validate_directory fails when file count is below threshold."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create only 1 file
        (Path(tmpdir) / "file_0.txt").write_text("data")
        
        result = validate_directory(Path(tmpdir), "Test Dir", min_files=5)
        assert result is False


def test_validate_directory_missing():
    """Test validate_directory fails for non-existent path."""
    path = Path("/tmp/non_existent_dir_999")
    result = validate_directory(path, "Missing Dir", min_files=0)
    assert result is False


def test_log_status_output():
    """Test that log_status prints correctly (visual check mostly, but we can assert return)."""
    # Just verify it returns the boolean passed
    assert log_status("Test message", True) is True
    assert log_status("Test message", False) is False