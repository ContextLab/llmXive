"""
Tests for the UCI Dataset Downloader module.
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_uci_datasets import (
    ensure_data_directory,
    fetch_dataset,
    clean_missing_values,
    DATASETS,
    compute_sha256
)


class TestEnsureDataDirectory:
    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that ensure_data_directory creates the directory if it doesn't exist."""
        test_dir = tmp_path / "new_dir"
        result = ensure_data_directory(str(test_dir))
        assert result.exists()
        assert result.is_dir()

    def test_returns_existing_directory(self, tmp_path):
        """Test that ensure_data_directory returns existing directory."""
        result = ensure_data_directory(str(tmp_path))
        assert result == tmp_path
        assert result.exists()


class TestComputeSha256:
    def test_compute_sha256(self, tmp_path):
        """Test SHA256 computation on a simple file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        checksum = compute_sha256(test_file)
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA256 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        checksum = compute_sha256(test_file)
        # Known SHA256 for empty file
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected


class TestFetchDataset:
    def test_fetch_dataset_success(self, tmp_path):
        """Test successful dataset fetch (mocked)."""
        # Mock the urllib request
        mock_response = MagicMock()
        mock_response.read.return_value = b"1,2,3\n4,5,6"

        with patch('urllib.request.urlopen', return_value=mock_response):
            success, message = fetch_dataset("wine", tmp_path)

        assert success is True
        assert "Downloaded successfully" in message
        assert (tmp_path / "wine.csv").exists()

    def test_fetch_dataset_already_exists(self, tmp_path):
        """Test that fetch skips if file already exists."""
        # Create the file first
        output_path = tmp_path / "wine.csv"
        output_path.write_text("existing data")

        # Mock urlopen to verify it's NOT called
        with patch('urllib.request.urlopen') as mock_urlopen:
            success, message = fetch_dataset("wine", tmp_path)

        assert success is True
        assert "Already exists" in message
        mock_urlopen.assert_not_called()

    def test_fetch_dataset_url_error(self, tmp_path):
        """Test handling of URL error."""
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Connection failed")):
            success, message = fetch_dataset("wine", tmp_path)

        assert success is False
        assert "Failed to fetch" in message

    def test_fetch_dataset_timeout(self, tmp_path):
        """Test handling of timeout error."""
        with patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Timeout")):
            success, message = fetch_dataset("ionosphere", tmp_path)

        assert success is False
        assert "Failed to fetch" in message


class TestCleanMissingValues:
    def test_clean_missing_values_no_missing(self, tmp_path):
        """Test cleaning when there are no missing values."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        input_file.write_text("1,2,3\n4,5,6\n7,8,9")

        result = clean_missing_values(input_file, output_file)

        assert result is True
        assert output_file.exists()
        content = output_file.read_text().strip()
        assert content == "1,2,3\n4,5,6\n7,8,9"

    def test_clean_missing_values_with_missing(self, tmp_path):
        """Test cleaning when there are missing values."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        input_file.write_text("1,2,3\n4,?,6\n7,8,9\n?,?,?")

        result = clean_missing_values(input_file, output_file)

        assert result is True
        assert output_file.exists()
        content = output_file.read_text().strip()
        # Should only keep rows without '?'
        lines = content.split('\n')
        assert len(lines) == 2
        assert "1,2,3" in lines
        assert "7,8,9" in lines

    def test_clean_missing_values_empty_file(self, tmp_path):
        """Test cleaning an empty file."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        input_file.write_text("")

        result = clean_missing_values(input_file, output_file)

        assert result is False  # Should return False for empty file
        assert not output_file.exists()


class TestDatasetsConfig:
    def test_all_required_datasets_defined(self):
        """Verify all required datasets are in the DATASETS config."""
        required_keys = [
            "wine",
            "wine_quality_red",
            "wine_quality_white",
            "ionosphere",
            "heart_cleveland"
        ]

        for key in required_keys:
            assert key in DATASETS, f"Missing dataset: {key}"
            assert "url" in DATASETS[key], f"Missing URL for {key}"
            assert "output_name" in DATASETS[key], f"Missing output_name for {key}"
