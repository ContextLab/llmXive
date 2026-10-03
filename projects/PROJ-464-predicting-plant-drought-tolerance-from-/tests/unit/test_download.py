import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from huggingface_hub import RepositoryNotFoundError, LocalEntryNotFoundError

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download_images import main, get_hf_files_list, verify_checksums, compute_sha256

class TestDownloadImages:
    """Tests for download_images.py focusing on loud failure on fetch errors."""

    @patch('download_images.api.list_repo_files')
    @patch('download_images.snapshot_download')
    def test_download_fails_loudly_repo_not_found(self, mock_snapshot, mock_list_files):
        """
        Test that the script raises RuntimeError with the exact message
        "No real NPPN root images found. Pipeline cannot proceed."
        when the repository is not found.
        """
        mock_list_files.side_effect = RepositoryNotFoundError("Repo not found")

        with pytest.raises(RuntimeError) as excinfo:
            main()

        assert str(excinfo.value) == "No real NPPN root images found. Pipeline cannot proceed."

    @patch('download_images.api.list_repo_files')
    @patch('download_images.snapshot_download')
    def test_download_fails_loudly_local_entry_not_found(self, mock_snapshot, mock_list_files):
        """
        Test that the script raises RuntimeError with the exact message
        when LocalEntryNotFoundError occurs.
        """
        mock_list_files.return_value = ["image.png"]
        mock_snapshot.side_effect = LocalEntryNotFoundError("Local entry not found")

        with pytest.raises(RuntimeError) as excinfo:
            main()

        assert str(excinfo.value) == "No real NPPN root images found. Pipeline cannot proceed."

    @patch('download_images.api.list_repo_files')
    @patch('download_images.snapshot_download')
    def test_download_fails_loudly_empty_repo(self, mock_snapshot, mock_list_files):
        """
        Test that the script raises RuntimeError if no image files are found in the repo.
        """
        mock_list_files.return_value = ["readme.txt"] # No images

        with pytest.raises(RuntimeError) as excinfo:
            main()

        assert str(excinfo.value) == "No real NPPN root images found. Pipeline cannot proceed."

    @patch('download_images.HfApi')
    def test_get_hf_files_list_no_images(self, mock_api_class):
        """Test get_hf_files_list raises when no matching files exist."""
        mock_api = MagicMock()
        mock_api.list_repo_files.return_value = ["readme.md", "data.csv"]
        mock_api_class.return_value = mock_api

        with pytest.raises(RuntimeError) as excinfo:
            get_hf_files_list(mock_api, "fake/repo", ["*.png"])

        assert "No image files found" in str(excinfo.value)

    def test_compute_sha256(self, tmp_path):
        """Test SHA256 computation on a real file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        hash_val = compute_sha256(test_file)
        # Known SHA256 for "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert hash_val == expected

    def test_verify_checksums_mismatch(self, tmp_path):
        """Test verify_checksums returns False on mismatch."""
        file_a = tmp_path / "a.txt"
        file_a.write_text("content")

        checksums = {"a.txt": "wrong_hash"}

        assert verify_checksums(tmp_path, checksums) is False

    def test_verify_checksums_match(self, tmp_path):
        """Test verify_checksums returns True on match."""
        file_a = tmp_path / "a.txt"
        file_a.write_text("content")

        # Compute actual hash
        from download_images import compute_sha256
        actual_hash = compute_sha256(file_a)

        checksums = {"a.txt": actual_hash}

        assert verify_checksums(tmp_path, checksums) is True

    @patch('download_images.snapshot_download')
    @patch('download_images.api.list_repo_files')
    def test_download_fails_loudly_generic_exception(self, mock_list, mock_snapshot):
        """Test that generic exceptions during download are caught and re-raised as the standard error."""
        mock_list.return_value = ["img.png"]
        mock_snapshot.side_effect = Exception("Network timeout")

        with pytest.raises(RuntimeError) as excinfo:
            main()

        assert str(excinfo.value) == "No real NPPN root images found. Pipeline cannot proceed."
        assert excinfo.value.__cause__ is not None