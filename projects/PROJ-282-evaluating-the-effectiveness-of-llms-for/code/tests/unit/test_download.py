import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from src.data.download import (
    compute_sha256,
    verify_checksum,
    download_via_wget,
    clone_via_git,
    validate_dataset,
    download_all_datasets,
    DATASET_CONFIGS
)

class TestChecksumFunctions:
    def test_compute_sha256_success(self, tmp_path):
        """Test SHA256 computation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = compute_sha256(test_file)
        
        # Known SHA256 for "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected

    def test_compute_sha256_empty_file(self, tmp_path):
        """Test SHA256 computation on an empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        checksum = compute_sha256(test_file)
        
        # Known SHA256 for empty file
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected

    def test_compute_sha256_not_found(self, tmp_path):
        """Test SHA256 computation on non-existent file raises error."""
        test_file = tmp_path / "nonexistent.txt"
        
        with pytest.raises(FileNotFoundError):
            compute_sha256(test_file)

class TestDownloadFunctions:
    @patch('src.data.download.requests.get')
    def test_download_via_wget_success(self, mock_get, tmp_path):
        """Test successful file download."""
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.headers.get.return_value = "100"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        result = download_via_wget(
            "http://example.com/test.zip",
            tmp_path,
            "test.zip"
        )
        
        assert result.exists()
        assert result.read_bytes() == b"test data"
        mock_get.assert_called_once()

    @patch('src.data.download.subprocess.run')
    def test_clone_via_git_success(self, mock_run, tmp_path):
        """Test successful git clone."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = clone_via_git(
            "http://example.com/repo.git",
            tmp_path / "repo"
        )
        
        assert result.exists()
        mock_run.assert_called_once()

    def test_clone_via_git_failure(self, tmp_path):
        """Test git clone failure raises error."""
        with patch('src.data.download.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Clone failed")
            
            with pytest.raises(RuntimeError):
                clone_via_git("http://example.com/repo.git", tmp_path / "repo")

class TestValidation:
    def test_validate_unknown_dataset(self, tmp_path):
        """Test validation of unknown dataset name."""
        is_valid, message = validate_dataset("unknown_dataset", tmp_path)
        
        assert not is_valid
        assert "Unknown dataset" in message

    def test_validate_url_dataset_missing_file(self, tmp_path):
        """Test validation of URL dataset with missing file."""
        with patch.dict(DATASET_CONFIGS, {
            "test": {
                "type": "url",
                "filename": "missing.zip",
                "extract_dir": "extracted"
            }
        }, clear=False):
            is_valid, message = validate_dataset("test", tmp_path)
            
            assert not is_valid
            assert "Missing file" in message

    def test_validate_git_dataset_success(self, tmp_path):
        """Test validation of successful git clone."""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        (repo_dir / "test.c").write_text("int main() {}")
        
        with patch.dict(DATASET_CONFIGS, {
            "test": {
                "type": "git",
                "target_dir": "test_repo"
            }
        }, clear=False):
            is_valid, message = validate_dataset("test", tmp_path)
            
            assert is_valid
            assert "validated successfully" in message

class TestDownloadAllDatasets:
    @patch('src.data.download.download_via_wget')
    @patch('src.data.download.clone_via_git')
    def test_download_all_success(self, mock_clone, mock_download, tmp_path):
        """Test downloading all datasets succeeds."""
        mock_download.return_value = tmp_path / "test.zip"
        mock_clone.return_value = tmp_path / "test_repo"
        
        # Create necessary directories and files for validation
        extracted_dir = tmp_path / "VulDeePecker-Dataset-main"
        extracted_dir.mkdir()
        (extracted_dir / "test.c").write_text("int main() {}")
        
        (tmp_path / "juliet-c-tests").mkdir()
        (tmp_path / "juliet-c-tests" / ".git").mkdir()
        (tmp_path / "juliet-c-tests" / "test.c").write_text("int main() {}")
        
        results = download_all_datasets(tmp_path, validate=True)
        
        assert all(results.values())

    @patch('src.data.download.download_via_wget')
    def test_download_all_failure(self, mock_download, tmp_path):
        """Test downloading datasets fails loudly on error."""
        mock_download.side_effect = RuntimeError("Download failed")
        
        with pytest.raises(RuntimeError):
            download_all_datasets(tmp_path, validate=True)