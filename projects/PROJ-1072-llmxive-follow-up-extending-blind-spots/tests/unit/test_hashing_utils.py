"""
Unit tests for hashing_utils.py
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from code.utils.hashing_utils import (
    compute_file_hash,
    compute_string_hash,
    compute_bytes_hash,
    compute_dict_hash,
    hash_artifact,
    verify_file_hash,
)


class TestComputeFileHash:
    def test_hash_of_known_file(self, tmp_path):
        """Test hashing a file with known content."""
        content = b"Hello, World!"
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(content)

        # SHA-256 of "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        actual_hash = compute_file_hash(file_path)

        assert actual_hash == expected_hash

    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_hash(non_existent)

    def test_different_algorithms(self, tmp_path):
        """Test that different algorithms produce different hashes."""
        content = b"Test content"
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(content)

        sha256_hash = compute_file_hash(file_path, "sha256")
        md5_hash = compute_file_hash(file_path, "md5")

        assert sha256_hash != md5_hash
        assert len(sha256_hash) == 64  # SHA-256 produces 64 hex chars
        assert len(md5_hash) == 32  # MD5 produces 32 hex chars


class TestComputeStringHash:
    def test_hash_of_known_string(self):
        """Test hashing a string with known content."""
        content = "Hello, World!"
        # SHA-256 of "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        actual_hash = compute_string_hash(content)

        assert actual_hash == expected_hash

    def test_empty_string(self):
        """Test hashing an empty string."""
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        actual_hash = compute_string_hash("")
        assert actual_hash == expected_hash


class TestComputeBytesHash:
    def test_hash_of_known_bytes(self):
        """Test hashing bytes with known content."""
        content = b"Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        actual_hash = compute_bytes_hash(content)

        assert actual_hash == expected_hash

    def test_empty_bytes(self):
        """Test hashing empty bytes."""
        expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        actual_hash = compute_bytes_hash(b"")
        assert actual_hash == expected_hash


class TestComputeDictHash:
    def test_hash_determinism(self):
        """Test that dict hashing is deterministic regardless of key order."""
        dict1 = {"b": 2, "a": 1}
        dict2 = {"a": 1, "b": 2}

        hash1 = compute_dict_hash(dict1)
        hash2 = compute_dict_hash(dict2)

        assert hash1 == hash2

    def test_hash_content_sensitivity(self):
        """Test that different content produces different hashes."""
        dict1 = {"a": 1}
        dict2 = {"a": 2}

        hash1 = compute_dict_hash(dict1)
        hash2 = compute_dict_hash(dict2)

        assert hash1 != hash2

    def test_hash_nested_dict(self):
        """Test hashing a nested dictionary."""
        dict1 = {"outer": {"inner": "value"}}
        dict2 = {"outer": {"inner": "value"}}
        dict3 = {"outer": {"inner": "different"}}

        assert compute_dict_hash(dict1) == compute_dict_hash(dict2)
        assert compute_dict_hash(dict1) != compute_dict_hash(dict3)


class TestHashArtifact:
    def test_hash_artifact_without_metadata(self, tmp_path):
        """Test hashing an artifact without metadata."""
        content = b"Test artifact content"
        file_path = tmp_path / "artifact.txt"
        file_path.write_bytes(content)

        file_hash = compute_file_hash(file_path)
        returned_hash = hash_artifact(file_path)

        assert returned_hash == file_hash

    def test_hash_artifact_with_metadata(self, tmp_path):
        """Test hashing an artifact with metadata."""
        content = b"Test artifact content"
        file_path = tmp_path / "artifact.txt"
        file_path.write_bytes(content)

        metadata = {"version": "1.0", "author": "test"}
        returned_hash = hash_artifact(file_path, metadata=metadata)

        assert returned_hash == compute_file_hash(file_path)

    def test_hash_artifact_with_output(self, tmp_path):
        """Test hashing an artifact and writing the record."""
        content = b"Test artifact content"
        file_path = tmp_path / "artifact.txt"
        file_path.write_bytes(content)

        output_path = tmp_path / "hash_record.json"
        hash_artifact(file_path, output_path=output_path)

        assert output_path.exists()

        with open(output_path, "r") as f:
            record = json.load(f)

        assert record["file"] == str(file_path)
        assert record["hash"] == compute_file_hash(file_path)
        assert record["algorithm"] == "sha256"


class TestVerifyFileHash:
    def test_verify_correct_hash(self, tmp_path):
        """Test verifying a file with the correct hash."""
        content = b"Test content"
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(content)

        correct_hash = compute_file_hash(file_path)
        assert verify_file_hash(file_path, correct_hash) is True

    def test_verify_incorrect_hash(self, tmp_path):
        """Test verifying a file with an incorrect hash."""
        content = b"Test content"
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(content)

        wrong_hash = "a" * 64
        assert verify_file_hash(file_path, wrong_hash) is False

    def test_verify_file_not_found(self, tmp_path):
        """Test verifying a non-existent file."""
        non_existent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            verify_file_hash(non_existent, "a" * 64)