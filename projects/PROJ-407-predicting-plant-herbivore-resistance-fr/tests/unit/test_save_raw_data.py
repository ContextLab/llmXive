"""
Unit tests for code/save_raw_data.py (Task T014).
"""
import os
import tempfile
import hashlib
from pathlib import Path
import pytest
import pandas as pd

# Import the function to test
from save_raw_data import compute_sha256, main
import sys
from io import StringIO

def test_compute_sha256_valid_file():
    """Test compute_sha256 with a valid file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("col1,col2\n1,2\n3,4\n")
        temp_path = f.name

    try:
        hash1 = compute_sha256(temp_path)
        hash2 = compute_sha256(temp_path)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    finally:
        os.unlink(temp_path)

def test_compute_sha256_file_not_found():
    """Test compute_sha256 raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.csv")

def test_compute_sha256_empty_file():
    """Test compute_sha256 raises ValueError for empty file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        temp_path = f.name

    try:
        # Ensure file is empty
        with open(temp_path, 'w') as _:
            pass

        with pytest.raises(ValueError):
            compute_sha256(temp_path)
    finally:
        os.unlink(temp_path)

def test_main_integration(tmp_path):
    """Test main function creates checksum file correctly."""
    # Create a sample CSV
    sample_csv = tmp_path / "test_data.csv"
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    df.to_csv(sample_csv, index=False)

    output_dir = tmp_path / "output"
    output_dir.mkdir()

    # Mock sys.argv
    original_argv = sys.argv
    sys.argv = [
        "test_save_raw_data.py",
        "--input", str(sample_csv),
        "--output_dir", str(output_dir)
    ]

    try:
        main()

        # Check checksum file exists
        checksum_file = output_dir / "test_data.csv.sha256"
        assert checksum_file.exists()

        # Verify content format
        with open(checksum_file, 'r') as f:
            content = f.read()
            parts = content.split()
            assert len(parts) == 2
            assert len(parts[0]) == 64  # Hash length
            assert parts[1] == "test_data.csv"

        # Verify hash correctness
        expected_hash = hashlib.sha256(sample_csv.read_bytes()).hexdigest()
        assert parts[0] == expected_hash

    finally:
        sys.argv = original_argv

def test_main_missing_input():
    """Test main exits with error when input file is missing."""
    original_argv = sys.argv
    sys.argv = [
        "test_save_raw_data.py",
        "--input", "/nonexistent/file.csv",
        "--output_dir", "/tmp"
    ]

    try:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    finally:
        sys.argv = original_argv