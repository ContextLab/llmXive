"""
Unit tests for the dataset verification script.
"""

import os
import json
import hashlib
from pathlib import Path

import pytest

# Import the functions from the newly added script
from code.verify_dataset import (
    download_test_shard,
    compute_sha256,
    write_checksum_record,
    DEFAULT_DATASET_ID,
    TEST_SHARD_SIZE,
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory and patch the data paths to use it."""
    # Patch the get_data_path function to point inside tmp_path
    from code import config

    original_get_data_path = config.get_data_path

    def get_data_path_mock(*parts):
        return Path(tmp_path, *parts)

    config.get_data_path = get_data_path_mock
    yield tmp_path
    # Restore original function after test
    config.get_data_path = original_get_data_path

def test_download_test_shard_creates_file(temp_dir):
    shard_path = download_test_shard()
    assert shard_path.is_file()
    # Verify that the file contains the expected number of lines
    with shard_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) == TEST_SHARD_SIZE

def test_compute_sha256_matches_file_content(temp_dir):
    # Create a known file
    test_file = Path(temp_dir, "known.txt")
    content = b"hello world"
    test_file.write_bytes(content)

    expected_checksum = hashlib.sha256(content).hexdigest()
    computed = compute_sha256(test_file)
    assert computed == expected_checksum

def test_write_checksum_record_creates_file(temp_dir):
    checksum_file = Path(temp_dir, "checksums.txt")
    write_checksum_record(DEFAULT_DATASET_ID, "deadbeef", checksum_file)
    assert checksum_file.is_file()
    with checksum_file.open("r", encoding="utf-8") as f:
        line = f.read().strip()
    assert line == f"{DEFAULT_DATASET_ID}  deadbeef"