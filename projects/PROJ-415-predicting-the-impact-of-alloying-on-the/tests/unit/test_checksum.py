"""
Unit tests for checksum utilities.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.data.checksum import (
    compute_sha256,
    generate_checksums,
    save_checksums,
    load_checksums,
    verify_checksums
)


def test_compute_sha256(tmp_path):
    """Test SHA256 computation on a known file."""
    test_file = tmp_path / "test.txt"
    content = "Hello, World!"
    test_file.write_text(content)

    hash_val = compute_sha256(test_file)

    # Known SHA256 for "Hello, World!"
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert hash_val == expected


def test_generate_checksums(tmp_path):
    """Test recursive checksum generation."""
    # Create directory structure
    (tmp_path / "subdir").mkdir()
    file1 = tmp_path / "file1.csv"
    file2 = tmp_path / "subdir" / "file2.json"
    file3 = tmp_path / "file3.txt"  # Should be excluded if filtering

    file1.write_text("data1")
    file2.write_text("data2")
    file3.write_text("data3")

    # Test all files
    checksums = generate_checksums(tmp_path)
    assert len(checksums) == 3
    assert "file1.csv" in checksums
    assert "subdir/file2.json" in checksums
    assert "file3.txt" in checksums

    # Test with extension filter
    checksums_csv = generate_checksums(tmp_path, extensions=[".csv"])
    assert len(checksums_csv) == 1
    assert "file1.csv" in checksums_csv


def test_save_and_load_checksums(tmp_path):
    """Test saving and loading checksums to/from JSON."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("test data")

    checksums = {"test.csv": compute_sha256(test_file)}
    output_path = tmp_path / "checksums.json"

    save_checksums(checksums, output_path)
    assert output_path.exists()

    loaded = load_checksums(output_path)
    assert loaded == checksums


def test_verify_checksums_success(tmp_path):
    """Test verification when files match."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("test data")

    checksums = {"test.csv": compute_sha256(test_file)}
    checksum_path = tmp_path / "checksums.json"
    save_checksums(checksums, checksum_path)

    with patch("code.data.checksum.DATA_DIR", tmp_path):
        assert verify_checksums(tmp_path, checksum_path) is True


def test_verify_checksums_missing_file(tmp_path):
    """Test verification when a file is missing."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("test data")

    checksums = {"test.csv": compute_sha256(test_file), "missing.csv": "fakehash"}
    checksum_path = tmp_path / "checksums.json"
    save_checksums(checksums, checksum_path)

    with patch("code.data.checksum.DATA_DIR", tmp_path):
        assert verify_checksums(tmp_path, checksum_path) is False


def test_verify_checksums_mismatch(tmp_path):
    """Test verification when file content changes."""
    test_file = tmp_path / "test.csv"
    test_file.write_text("original data")

    checksums = {"test.csv": compute_sha256(test_file)}
    checksum_path = tmp_path / "checksums.json"
    save_checksums(checksums, checksum_path)

    # Change file content
    test_file.write_text("modified data")

    with patch("code.data.checksum.DATA_DIR", tmp_path):
        assert verify_checksums(tmp_path, checksum_path) is False
