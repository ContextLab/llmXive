"""
Tests for the checksum utility module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils.checksum import (
    compute_sha256,
    verify_checksum,
    write_checksum_file,
    read_checksum_file,
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_checksum_file():
    """Create a temporary directory for checksum files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil

    shutil.rmtree(temp_dir)


def test_compute_sha256(temp_file):
    """Test that compute_sha256 returns a valid hex string."""
    checksum = compute_sha256(temp_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert all(c in "0123456789abcdef" for c in checksum.lower())


def test_compute_sha256_known_value(temp_file):
    """Test compute_sha256 against a known value."""
    # "Hello, World!" SHA256
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    checksum = compute_sha256(temp_file)
    assert checksum.lower() == expected


def test_compute_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")


def test_compute_sha256_not_a_file(temp_file):
    """Test that ValueError is raised for directories."""
    with pytest.raises(ValueError):
        compute_sha256(temp_file.rsplit("/", 1)[0])  # Pass the directory


def test_verify_checksum_match(temp_file):
    """Test verify_checksum returns True for matching checksum."""
    expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    assert verify_checksum(temp_file, expected) is True


def test_verify_checksum_mismatch(temp_file):
    """Test verify_checksum returns False for mismatching checksum."""
    wrong_checksum = "0" * 64
    assert verify_checksum(temp_file, wrong_checksum) is False


def test_verify_checksum_case_insensitive(temp_file):
    """Test that checksum verification is case-insensitive."""
    expected_upper = "DFFD6021BB2BD5B0AF676290809EC3A53191DD81C7F70A4B28688A362182986F"
    assert verify_checksum(temp_file, expected_upper) is True


def test_write_checksum_file(temp_file, temp_checksum_file):
    """Test write_checksum_file creates a file with the correct checksum."""
    output_path = Path(temp_checksum_file) / "checksum.txt"
    checksum = write_checksum_file(temp_file, output_path)

    assert output_path.exists()
    assert checksum == compute_sha256(temp_file)

    with open(output_path, "r") as f:
        content = f.read().strip()
    assert content == checksum


def test_read_checksum_file(temp_file, temp_checksum_file):
    """Test read_checksum_file retrieves the correct checksum."""
    output_path = Path(temp_checksum_file) / "checksum.txt"
    expected_checksum = write_checksum_file(temp_file, output_path)

    retrieved = read_checksum_file(output_path)
    assert retrieved == expected_checksum


def test_read_checksum_file_not_found(temp_checksum_file):
    """Test read_checksum_file returns None for missing file."""
    non_existent = Path(temp_checksum_file) / "nonexistent.txt"
    assert read_checksum_file(non_existent) is None