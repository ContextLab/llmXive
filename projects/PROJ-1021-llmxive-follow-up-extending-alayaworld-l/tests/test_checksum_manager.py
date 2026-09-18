"""
Tests for the checksum manager module.
"""

import json
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to add the project root to the path to import code/data
# Assuming tests are in projects/.../tests/ and code is in projects/.../code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(CODE_DIR))

from data.checksum_manager import (
    calculate_sha256,
    generate_checksums,
    save_checksums,
    load_checksums,
    verify_integrity,
    DATA_DIR,
    CHECKSUM_FILE
)


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data dir."""
    # Create a temp structure
    temp_root = tmp_path / "temp_project"
    temp_data = temp_root / "data"
    temp_data.mkdir(parents=True)

    # Create some dummy files
    (temp_data / "file1.txt").write_text("Hello World")
    (temp_data / "file2.json").write_text('{"key": "value"}')
    (temp_data / "subdir").mkdir()
    (temp_data / "subdir" / "file3.bin").write_bytes(b"\x00\x01\x02")

    # Create a hidden file (should be ignored)
    (temp_data / ".hidden").write_text("Secret")

    # Temporarily override the global DATA_DIR constant
    # Note: In a real scenario, we might refactor the module to accept a root path,
    # but for now we will test the functions that take explicit paths or rely on the fixture
    # by monkeypatching the module's global if necessary, or just testing logic that doesn't depend on global DATA_DIR.
    # However, generate_checksums and verify_integrity use global DATA_DIR.
    # We will test calculate_sha256 and save/load directly, and mock the others.

    return temp_root, temp_data


def test_calculate_sha256(temp_data_dir):
    """Test SHA256 calculation on a known string."""
    _, temp_data = temp_data_dir
    file_path = temp_data / "file1.txt"
    hash_val = calculate_sha256(file_path)
    # "Hello World" SHA256
    expected = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
    assert hash_val == expected


def test_calculate_sha256_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256(Path("/nonexistent/file.txt"))


def test_calculate_sha256_directory():
    """Test error handling for directory."""
    with pytest.raises(IsADirectoryError):
        calculate_sha256(Path("/tmp"))


def test_save_and_load_checksums(temp_data_dir):
    """Test saving and loading checksums."""
    temp_root, temp_data = temp_data_dir
    # Create a mock checksum dict relative to temp_data
    checksums = {
        "file1.txt": "hash1",
        "subdir/file3.bin": "hash2"
    }

    output_path = temp_root / "data" / ".test_checksums.json"
    save_path = save_checksums(checksums, output_path)

    assert save_path.exists()
    with open(save_path, "r") as f:
        data = json.load(f)
    assert data["checksums"] == checksums

    loaded = load_checksums(output_path)
    assert loaded == checksums


def test_verify_integrity_success(temp_data_dir):
    """Test successful verification."""
    temp_root, temp_data = temp_data_dir
    # Create a real file and calculate its hash
    file_path = temp_data / "verify_test.txt"
    file_path.write_text("Test Content")
    real_hash = calculate_sha256(file_path)

    checksums = {
        "verify_test.txt": real_hash
    }
    output_path = temp_root / "data" / ".test_checksums.json"
    save_checksums(checksums, output_path)

    # Temporarily patch DATA_DIR for the test
    import data.checksum_manager as cm
    original_data_dir = cm.DATA_DIR
    cm.DATA_DIR = temp_data
    original_checksum_file = cm.CHECKSUM_FILE
    cm.CHECKSUM_FILE = output_path

    try:
        is_valid, failures = verify_integrity()
        assert is_valid
        assert len(failures) == 0
    finally:
        cm.DATA_DIR = original_data_dir
        cm.CHECKSUM_FILE = original_checksum_file


def test_verify_integrity_failure(temp_data_dir):
    """Test verification failure due to hash mismatch."""
    temp_root, temp_data = temp_data_dir
    file_path = temp_data / "bad_test.txt"
    file_path.write_text("Original")
    # Save wrong hash
    checksums = {
        "bad_test.txt": "wrong_hash_value"
    }
    output_path = temp_root / "data" / ".test_checksums.json"
    save_checksums(checksums, output_path)

    import data.checksum_manager as cm
    original_data_dir = cm.DATA_DIR
    cm.DATA_DIR = temp_data
    original_checksum_file = cm.CHECKSUM_FILE
    cm.CHECKSUM_FILE = output_path

    try:
        is_valid, failures = verify_integrity()
        assert not is_valid
        assert len(failures) == 1
        assert "bad_test.txt" in failures[0]
    finally:
        cm.DATA_DIR = original_data_dir
        cm.CHECKSUM_FILE = original_checksum_file


def test_verify_integrity_missing_file(temp_data_dir):
    """Test verification failure due to missing file."""
    temp_root, temp_data = temp_data_dir
    checksums = {
        "missing_file.txt": "some_hash"
    }
    output_path = temp_root / "data" / ".test_checksums.json"
    save_checksums(checksums, output_path)

    import data.checksum_manager as cm
    original_data_dir = cm.DATA_DIR
    cm.DATA_DIR = temp_data
    original_checksum_file = cm.CHECKSUM_FILE
    cm.CHECKSUM_FILE = output_path

    try:
        is_valid, failures = verify_integrity()
        assert not is_valid
        assert len(failures) == 1
        assert "missing" in failures[0].lower()
    finally:
        cm.DATA_DIR = original_data_dir
        cm.CHECKSUM_FILE = original_checksum_file
