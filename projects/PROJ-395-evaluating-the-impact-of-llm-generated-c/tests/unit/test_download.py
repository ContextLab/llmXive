"""
Unit tests for code/download.py.

These tests verify that the download module correctly attempts to fetch
real datasets from HuggingFace and handles errors appropriately.

Note: These tests require network access and valid HuggingFace credentials
(if the datasets are gated, though HumanEval and MBPP are public).
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download import (
    download_humaneval,
    download_mbpp,
    _calculate_sha256,
    _verify_checksum,
    DATA_RAW_DIR
)


class TestChecksumUtils:
    """Tests for helper functions."""

    def test_calculate_sha256(self):
        """Test SHA256 calculation on a known string."""
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            # Known hash for "test content"
            expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
            actual_hash = _calculate_sha256(Path(temp_path))
            assert actual_hash == expected_hash, f"Expected {expected_hash}, got {actual_hash}"
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_missing_file(self):
        """Test verification fails for missing file."""
        assert _verify_checksum(Path("/nonexistent/file.txt")) is False

    def test_verify_checksum_empty_file(self):
        """Test verification fails for empty file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
        
        try:
            assert _verify_checksum(Path(temp_path)) is False
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_valid_file(self):
        """Test verification passes for valid file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("valid content")
            temp_path = f.name
        
        try:
            assert _verify_checksum(Path(temp_path)) is True
        finally:
            os.unlink(temp_path)


class TestDownloadFunctions:
    """Tests for download functions (mocked)."""

    @patch('code.download.load_dataset')
    @patch('code.download.DATA_RAW_DIR', new=MagicMock())
    def test_download_humaneval_success(self, mock_load_dataset, mock_dir):
        """Test successful HumanEval download."""
        # Setup mocks
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset
        mock_dir.mkdir.return_value = None
        mock_dir.__truediv__.return_value = Path("/fake/path.parquet")
        
        # Mock the to_parquet method
        mock_dataset.to_parquet = MagicMock()
        
        # Mock checksum verification to return True
        with patch('code.download._verify_checksum', return_value=True):
            result = download_humaneval()
            
            # Verify calls
            mock_load_dataset.assert_called_once()
            mock_dataset.to_parquet.assert_called_once()
            assert result == Path("/fake/path.parquet")

    @patch('code.download.load_dataset')
    def test_download_humaneval_failure(self, mock_load_dataset):
        """Test HumanEval download raises error on failure."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with patch('code.download.DATA_RAW_DIR', new=MagicMock()):
            with pytest.raises(RuntimeError) as exc_info:
                download_humaneval()
            
            assert "Failed to download HumanEval" in str(exc_info.value)

    @patch('code.download.load_dataset')
    @patch('code.download.DATA_RAW_DIR', new=MagicMock())
    def test_download_mbpp_success(self, mock_load_dataset, mock_dir):
        """Test successful MBPP download."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset
        mock_dir.mkdir.return_value = None
        mock_dir.__truediv__.return_value = Path("/fake/path.parquet")
        mock_dataset.to_parquet = MagicMock()
        
        with patch('code.download._verify_checksum', return_value=True):
            result = download_mbpp()
            
            mock_load_dataset.assert_called_once()
            mock_dataset.to_parquet.assert_called_once()
            assert result == Path("/fake/path.parquet")

    @patch('code.download.load_dataset')
    def test_download_mbpp_failure(self, mock_load_dataset):
        """Test MBPP download raises error on failure."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with patch('code.download.DATA_RAW_DIR', new=MagicMock()):
            with pytest.raises(RuntimeError) as exc_info:
                download_mbpp()
            
            assert "Failed to download MBPP" in str(exc_info.value)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
