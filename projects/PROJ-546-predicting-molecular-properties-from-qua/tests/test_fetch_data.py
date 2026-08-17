"""
Contract tests for fetch_data.py.

These tests verify that the Zenodo fetch and data validity requirements are met.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.fetch_data import (
    compute_sha256,
    download_file,
    verify_checksum,
    extract_tarball,
    convert_to_csv,
    fetch_and_verify_data,
    setup_logger,
)


class TestComputeSHA256:
    def test_compute_sha256_on_known_file(self, tmp_path):
        """Test SHA-256 computation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        expected_hash = hashlib.sha256(test_content).hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA-256 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")

        expected_hash = hashlib.sha256(b"").hexdigest()
        actual_hash = compute_sha256(test_file)

        assert actual_hash == expected_hash


class TestDownloadFile:
    @patch('code.fetch_data.requests.get')
    def test_download_file_success(self, mock_get, tmp_path):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.headers = {'content-length': '9'}
        mock_get.return_value = mock_response

        test_file = tmp_path / "downloaded.txt"
        result = download_file("http://example.com/file", test_file, MagicMock())

        assert result is True
        assert test_file.exists()
        assert test_file.read_bytes() == b"test data"

    @patch('code.fetch_data.requests.get')
    def test_download_file_failure(self, mock_get, tmp_path):
        """Test failed file download."""
        mock_get.side_effect = Exception("Network error")

        test_file = tmp_path / "downloaded.txt"
        result = download_file("http://example.com/file", test_file, MagicMock())

        assert result is False
        assert not test_file.exists()


class TestVerifyChecksum:
    def test_verify_checksum_match(self, tmp_path):
        """Test checksum verification with matching checksums."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)

        expected_hash = hashlib.sha256(test_content).hexdigest()
        result = verify_checksum(test_file, expected_hash, MagicMock())

        assert result is True

    def test_verify_checksum_mismatch(self, tmp_path):
        """Test checksum verification with mismatched checksums."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"Hello, World!")

        result = verify_checksum(test_file, "wrong_hash", MagicMock())

        assert result is False


class TestExtractTarball:
    def test_extract_tarball_success(self, tmp_path):
        """Test successful tarball extraction."""
        # Create a simple tarball for testing
        import tarfile
        tar_path = tmp_path / "test.tar.gz"
        
        with tarfile.open(tar_path, "w:gz") as tar:
            # Add a test file
            test_file = tmp_path / "test.txt"
            test_file.write_text("test content")
            tar.add(test_file, arcname="test.txt")

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        result = extract_tarball(tar_path, extract_dir, MagicMock())

        assert result is True
        assert (extract_dir / "test.txt").exists()

    def test_extract_tarball_failure(self, tmp_path):
        """Test failed tarball extraction with invalid file."""
        invalid_tar = tmp_path / "invalid.tar.gz"
        invalid_tar.write_bytes(b"not a tar file")

        extract_dir = tmp_path / "extracted"
        extract_dir.mkdir()

        result = extract_tarball(invalid_tar, extract_dir, MagicMock())

        assert result is False


class TestConvertToCSV:
    def test_convert_to_csv_success(self, tmp_path):
        """Test successful CSV conversion from tarball."""
        import tarfile
        tar_path = tmp_path / "test.tar.gz"
        
        # Create a tarball with a CSV file
        with tarfile.open(tar_path, "w:gz") as tar:
            csv_file = tmp_path / "data.csv"
            csv_file.write_text("col1,col2\n1,2\n3,4")
            tar.add(csv_file, arcname="data.csv")

        output_csv = tmp_path / "output.csv"

        result = convert_to_csv(tar_path, output_csv, MagicMock())

        assert result is True
        assert output_csv.exists()
        assert "col1,col2" in output_csv.read_text()

    def test_convert_to_csv_no_csv(self, tmp_path):
        """Test CSV conversion when no CSV is found in tarball."""
        import tarfile
        tar_path = tmp_path / "test.tar.gz"
        
        # Create a tarball without CSV
        with tarfile.open(tar_path, "w:gz") as tar:
            txt_file = tmp_path / "data.txt"
            txt_file.write_text("not a csv")
            tar.add(txt_file, arcname="data.txt")

        output_csv = tmp_path / "output.csv"

        result = convert_to_csv(tar_path, output_csv, MagicMock())

        assert result is False


class TestFetchAndVerifyData:
    @patch('code.fetch_data.download_file')
    @patch('code.fetch_data.extract_tarball')
    @patch('code.fetch_data.convert_to_csv')
    @patch('code.fetch_data.verify_checksum')
    def test_fetch_and_verify_data_success(
        self, mock_verify, mock_convert, mock_extract, mock_download, tmp_path
    ):
        """Test successful data fetch and verification."""
        mock_download.return_value = True
        mock_extract.return_value = True
        mock_convert.return_value = True
        mock_verify.return_value = True

        # Mock the directory creation
        with patch('code.fetch_data.DATA_RAW_DIR', tmp_path):
            result = fetch_and_verify_data(MagicMock())

        assert result is True

    @patch('code.fetch_data.download_file')
    def test_fetch_and_verify_data_download_failure(self, mock_download, tmp_path):
        """Test failed data fetch due to download failure."""
        mock_download.return_value = False

        with patch('code.fetch_data.DATA_RAW_DIR', tmp_path):
            result = fetch_and_verify_data(MagicMock())

        assert result is False

    @patch('code.fetch_data.download_file')
    @patch('code.fetch_data.extract_tarball')
    def test_fetch_and_verify_data_extraction_failure(
        self, mock_extract, mock_download, tmp_path
    ):
        """Test failed data fetch due to extraction failure."""
        mock_download.return_value = True
        mock_extract.return_value = False

        with patch('code.fetch_data.DATA_RAW_DIR', tmp_path):
            result = fetch_and_verify_data(MagicMock())

        assert result is False

    @patch('code.fetch_data.download_file')
    @patch('code.fetch_data.extract_tarball')
    @patch('code.fetch_data.convert_to_csv')
    def test_fetch_and_verify_data_conversion_failure(
        self, mock_convert, mock_extract, mock_download, tmp_path
    ):
        """Test failed data fetch due to conversion failure."""
        mock_download.return_value = True
        mock_extract.return_value = True
        mock_convert.return_value = False

        with patch('code.fetch_data.DATA_RAW_DIR', tmp_path):
            result = fetch_and_verify_data(MagicMock())

        assert result is False

    @patch('code.fetch_data.download_file')
    @patch('code.fetch_data.extract_tarball')
    @patch('code.fetch_data.convert_to_csv')
    @patch('code.fetch_data.verify_checksum')
    def test_fetch_and_verify_data_checksum_failure(
        self, mock_verify, mock_convert, mock_extract, mock_download, tmp_path
    ):
        """Test failed data fetch due to checksum failure."""
        mock_download.return_value = True
        mock_extract.return_value = True
        mock_convert.return_value = True
        mock_verify.return_value = False

        with patch('code.fetch_data.DATA_RAW_DIR', tmp_path):
            result = fetch_and_verify_data(MagicMock())

        assert result is False


class TestSetupLogger:
    def test_setup_logger_creates_file(self, tmp_path, caplog):
        """Test that setup_logger creates the log file."""
        with patch('code.fetch_data.LOGS_DIR', tmp_path):
            logger = setup_logger()

        log_file = tmp_path / "verification.log"
        assert log_file.exists()

        # Log a message
        logger.info("Test message")

        # Check that the log file contains the message
        assert "Test message" in log_file.read_text()