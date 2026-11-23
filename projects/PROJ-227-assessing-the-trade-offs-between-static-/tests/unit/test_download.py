"""
Unit tests for the download module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
# We need to adjust the import path if running from tests/
import sys
from pathlib import Path

# Add the parent directory of tests to the path to import code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.download import (
    compute_file_checksum,
    verify_record,
    verify_dataset,
    load_checksums,
    save_checksums
)


class TestComputeChecksum:
    def test_compute_file_checksum(self, tmp_path):
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        checksum = compute_file_checksum(test_file)
        # SHA256 of "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert checksum == expected

    def test_compute_file_checksum_empty(self, tmp_path):
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        checksum = compute_file_checksum(test_file)
        # SHA256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected


class TestVerifyRecord:
    def test_valid_record(self):
        record = {"prompt": "def foo(): pass", "test": "assert foo() == 1"}
        assert verify_record(record) is True

    def test_missing_prompt(self):
        record = {"test": "assert foo() == 1"}
        assert verify_record(record) is False

    def test_missing_test(self):
        record = {"prompt": "def foo(): pass"}
        assert verify_record(record) is False

    def test_empty_prompt(self):
        record = {"prompt": "", "test": "assert foo() == 1"}
        assert verify_record(record) is False

    def test_empty_test(self):
        record = {"prompt": "def foo(): pass", "test": ""}
        assert verify_record(record) is False

    def test_not_dict(self):
        record = ["prompt", "test"]
        assert verify_record(record) is False


class TestVerifyDataset:
    def test_valid_dataset(self, tmp_path):
        data = [
            {"prompt": "def foo(): pass", "test": "assert foo() == 1"},
            {"prompt": "def bar(): pass", "test": "assert bar() == 2"},
        ]
        file_path = tmp_path / "valid.json"
        file_path.write_text(json.dumps(data))

        assert verify_dataset(file_path) is True

    def test_dataset_too_small(self, tmp_path):
        # Create a dataset with fewer than 100 records
        data = [{"prompt": "x", "test": "y"} for _ in range(50)]
        file_path = tmp_path / "small.json"
        file_path.write_text(json.dumps(data))

        assert verify_dataset(file_path) is False

    def test_invalid_json(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not json")

        assert verify_dataset(file_path) is False

    def test_missing_keys(self, tmp_path):
        data = [
            {"prompt": "x", "test": "y"},
            {"prompt": "a"}, # Missing test
        ]
        file_path = tmp_path / "bad.json"
        file_path.write_text(json.dumps(data))

        assert verify_dataset(file_path) is False

    def test_file_not_found(self, tmp_path):
        file_path = tmp_path / "nonexistent.json"
        assert verify_dataset(file_path) is False


class TestChecksumsIO:
    def test_load_checksums_new(self, tmp_path):
        # Mock the global paths to use tmp_path
        import code.download as download_module
        original_path = download_module.CHECKSUMS_FILE
        download_module.CHECKSUMS_FILE = tmp_path / "missing.json"
        
        try:
            result = load_checksums()
            assert result == {}
        finally:
            download_module.CHECKSUMS_FILE = original_path

    def test_save_and_load_checksums(self, tmp_path):
        import code.download as download_module
        original_path = download_module.CHECKSUMS_FILE
        test_file = tmp_path / "checksums.json"
        download_module.CHECKSUMS_FILE = test_file

        try:
            data = {"file1.txt": "abc123", "file2.txt": "def456"}
            save_checksums(data)
            
            loaded = load_checksums()
            assert loaded == data
        finally:
            download_module.CHECKSUMS_FILE = original_path