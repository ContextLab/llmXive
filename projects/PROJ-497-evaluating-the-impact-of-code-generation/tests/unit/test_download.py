"""
Contract test for dataset download integrity (T009).
Verifies that HumanEval and MBPP datasets are downloaded correctly,
checksums are computed and verified, and the saved checksums file
is created with the expected structure.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the functions from code/download.py
# Adjust the import path based on how the tests are run (e.g., PYTHONPATH)
# Assuming tests are run from project root:
sys_path = Path(__file__).parent.parent.parent / "code"
if str(sys_path) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(sys_path))

from download import (
    calculate_sha256,
    verify_checksums,
    save_checksums,
    load_saved_checksums,
    download_human_eval,
    download_mbpp,
)


class TestDownloadIntegrity:
    """Tests for dataset download integrity and checksum management."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield Path(tmpdirname)

    def test_calculate_sha256_file(self, temp_dir):
        """Verify SHA256 calculation for a real file."""
        test_file = temp_dir / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        hash_val = calculate_sha256(test_file)

        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash_val == expected, f"Hash mismatch: {hash_val} != {expected}"

    def test_calculate_sha256_nonexistent(self, temp_dir):
        """Verify SHA256 raises error for nonexistent file."""
        nonexistent = temp_dir / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            calculate_sha256(nonexistent)

    def test_save_and_load_checksums(self, temp_dir):
        """Verify checksums can be saved and loaded correctly."""
        checksums = {
            "file1.txt": "abc123...",
            "file2.txt": "def456...",
        }
        checksum_file = temp_dir / "checksums.json"

        save_checksums(checksums, checksum_file)

        assert checksum_file.exists(), "Checksum file was not created."

        loaded = load_saved_checksums(checksum_file)

        assert loaded == checksums, "Loaded checksums do not match saved ones."

    def test_load_nonexistent_checksums(self, temp_dir):
        """Verify loading from nonexistent file returns empty dict."""
        checksum_file = temp_dir / "nonexistent.json"
        loaded = load_saved_checksums(checksum_file)
        assert loaded == {}, "Expected empty dict for nonexistent file."

    def test_verify_checksums_success(self, temp_dir):
        """Verify checksum verification passes when hashes match."""
        test_file = temp_dir / "verify_test.txt"
        content = b"Test content"
        test_file.write_bytes(content)
        correct_hash = calculate_sha256(test_file)

        checksums = {"verify_test.txt": correct_hash}
        checksum_file = temp_dir / "checksums.json"
        save_checksums(checksums, checksum_file)

        # Move file to a different name to simulate directory structure if needed,
        # but verify_checksums expects a mapping of filename -> hash.
        # We'll test the logic directly with the dict.
        is_valid, failed = verify_checksums(checksums, temp_dir)

        assert is_valid is True, "Verification should pass."
        assert len(failed) == 0, "No files should have failed."

    def test_verify_checksums_failure(self, temp_dir):
        """Verify checksum verification fails when hashes mismatch."""
        test_file = temp_dir / "bad_hash.txt"
        test_file.write_bytes(b"Content")
        correct_hash = calculate_sha256(test_file)
        wrong_hash = "0" * 64  # Fake hash

        checksums = {"bad_hash.txt": wrong_hash}

        is_valid, failed = verify_checksums(checksums, temp_dir)

        assert is_valid is False, "Verification should fail."
        assert "bad_hash.txt" in failed, "bad_hash.txt should be in failed list."

    @patch("download.load_dataset_from_huggingface")
    def test_download_human_eval_mocked(self, mock_load, temp_dir):
        """Test HumanEval download logic with mocked dataset loading."""
        # Mock the dataset to return a simple object with 'save_to_disk'
        mock_dataset = type("Dataset", (), {"save_to_disk": lambda self, path: None})()
        mock_load.return_value = mock_dataset

        # Mock the checksum calculation to avoid file I/O for non-existent files
        with patch("download.calculate_sha256", return_value="mocked_hash"):
            # Mock save_checksums to avoid writing to disk
            with patch("download.save_checksums"):
                result = download_human_eval(temp_dir)

        assert result is True, "HumanEval download should return True on success."
        mock_load.assert_called_once()

    @patch("download.load_dataset_from_huggingface")
    def test_download_mbpp_mocked(self, mock_load, temp_dir):
        """Test MBPP download logic with mocked dataset loading."""
        mock_dataset = type("Dataset", (), {"save_to_disk": lambda self, path: None})()
        mock_load.return_value = mock_dataset

        with patch("download.calculate_sha256", return_value="mocked_hash"):
            with patch("download.save_checksums"):
                result = download_mbpp(temp_dir)

        assert result is True, "MBPP download should return True on success."
        mock_load.assert_called_once()

    def test_download_human_eval_real_source_exists(self):
        """
        Contract test: Verify that the HumanEval dataset can be loaded from HuggingFace.
        This test attempts a real download (or at least a load) to ensure the source is valid.
        It does not save to disk to keep the test fast and clean, but verifies the source is accessible.
        """
        from datasets import load_dataset
        # This is a real call to HuggingFace
        # We expect this to succeed if the dataset exists and network is available.
        # If it fails, the test fails, indicating a problem with the source or network.
        try:
            dataset = load_dataset("openai_humaneval", trust_remote_code=True)
            assert dataset is not None, "HumanEval dataset should not be None."
            assert "test" in dataset, "HumanEval dataset should have a 'test' split."
        except Exception as e:
            pytest.fail(f"Failed to load HumanEval from HuggingFace: {e}")

    def test_download_mbpp_real_source_exists(self):
        """
        Contract test: Verify that the MBPP dataset can be loaded from HuggingFace.
        Similar to HumanEval test, but for MBPP.
        """
        from datasets import load_dataset
        try:
            # MBPP is often available as 'mbpp' or 'google/mbpp'
            # Using the standard 'mbpp' identifier
            dataset = load_dataset("mbpp", split="train")
            assert dataset is not None, "MBPP dataset should not be None."
            assert len(dataset) > 0, "MBPP dataset should not be empty."
        except Exception as e:
            pytest.fail(f"Failed to load MBPP from HuggingFace: {e}")