import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from src.data.download import (
    compute_sha256, verify_checksum, download_via_wget, clone_via_git,
    validate_dataset, download_all_datasets, main
)


class TestChecksumFunctions:
    def test_compute_sha256(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            f.flush()
            hash_val = compute_sha256(Path(f.name))
            assert hash_val is not None
            os.unlink(f.name)

    def test_verify_checksum_success(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            f.flush()
            hash_val = compute_sha256(Path(f.name))
            assert verify_checksum(Path(f.name), hash_val) is True
            os.unlink(f.name)

    def test_verify_checksum_failure(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test")
            f.flush()
            assert verify_checksum(Path(f.name), "wrong_hash") is False
            os.unlink(f.name)

class TestDownloadFunctions:
    @patch('src.data.download.subprocess.run')
    def test_download_via_wget(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = download_via_wget("http://example.com", "/tmp")
        assert result is True

    @patch('src.data.download.subprocess.run')
    def test_clone_via_git(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = clone_via_git("https://github.com/example/repo", "/tmp")
        assert result is True

class TestValidation:
    def test_validate_dataset_missing_url(self):
        with pytest.raises(ValueError):
            validate_dataset({"name": "test"})

    def test_validate_dataset_invalid_url(self):
        with pytest.raises(ValueError):
            validate_dataset({"name": "test", "url": "not-a-url"})

class TestDownloadAllDatasets:
    @patch('src.data.download.download_via_wget')
    @patch('src.data.download.validate_dataset')
    def test_download_all_success(self, mock_validate, mock_download):
        mock_validate.return_value = True
        mock_download.return_value = True
        datasets = [{"name": "A", "url": "http://a.com"}]
        result = download_all_datasets(datasets, "/tmp")
        assert result is True
