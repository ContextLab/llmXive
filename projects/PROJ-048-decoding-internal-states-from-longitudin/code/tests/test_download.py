"""
Tests for data download functionality.
"""
import pytest
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import DownloadError, _calculate_sha256, _validate_checksum
from utils.memory_monitor import MemoryExceededError

class TestDownloadUtils:
    """Test utility functions for download module."""

    def test_calculate_sha256(self):
        """Test SHA256 calculation on a temporary file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            checksum = _calculate_sha256(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
            assert isinstance(checksum, str)
        finally:
            temp_path.unlink()

    def test_validate_checksum_match(self):
        """Test checksum validation when hashes match."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            checksum = _calculate_sha256(temp_path)
            assert _validate_checksum(temp_path, checksum) is True
        finally:
            temp_path.unlink()

    def test_validate_checksum_mismatch(self):
        """Test checksum validation when hashes don't match."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)
        
        try:
            assert _validate_checksum(temp_path, "wrong_checksum") is False
        finally:
            temp_path.unlink()

@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return {
        'DATASET_URL': 'https://example.com/allen',
        'MEMORY_LIMIT_GB': 5.0,
        'RANDOM_SEED': 42
    }

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@patch('data.download.get_dataset_url')
@patch('data.download.get_memory_limit_gb')
@patch('data.download.check_memory_limit')
class TestDownloadFlow:
    """Test download flow with mocked dependencies."""

    def test_download_success(
        self, 
        mock_check_memory, 
        mock_get_memory_limit, 
        mock_get_url,
        mock_config,
        temp_data_dir
    ):
        """Test successful download flow."""
        mock_get_url.return_value = mock_config['DATASET_URL']
        mock_get_memory_limit.return_value = mock_config['MEMORY_LIMIT_GB']
        
        # Create mock files
        roi_file = temp_data_dir / "roi_traces.h5"
        meta_file = temp_data_dir / "roi_metadata.json"
        
        # Write mock data
        roi_file.write_bytes(b"mock hdf5 data")
        meta_file.write_text(json.dumps({
            'experiment_id': 'exp_001',
            'subject_id': 'sub_001',
            'acquisition_date': '2024-01-01',
            'num_rois': 100
        }))
        
        # Mock the download function to use temp directory
        with patch('data.download.ROIS_FILE', roi_file):
            with patch('data.download.METADATA_FILE', meta_file):
                with patch('data.download.DATA_DIR', temp_data_dir):
                    with patch('data.download._download_file') as mock_download:
                        mock_download.side_effect = lambda url, path, desc: path
                        
                        from data.download import download_allen_data
                        roi_path, meta_path = download_allen_data()
                        
                        assert roi_path.exists()
                        assert meta_path.exists()

    def test_memory_limit_exceeded(
        self, 
        mock_check_memory, 
        mock_get_memory_limit, 
        mock_get_url,
        temp_data_dir
    ):
        """Test that memory limit is enforced."""
        mock_get_url.return_value = mock_config['DATASET_URL']
        mock_get_memory_limit.return_value = mock_config['MEMORY_LIMIT_GB']
        mock_check_memory.side_effect = MemoryExceededError("Memory limit exceeded")
        
        with patch('data.download.DATA_DIR', temp_data_dir):
            from data.download import download_allen_data
            
            with pytest.raises(MemoryExceededError):
                download_allen_data()

    def test_missing_dataset_url(
        self, 
        mock_check_memory, 
        mock_get_memory_limit, 
        mock_get_url,
        temp_data_dir
    ):
        """Test error when DATASET_URL is missing."""
        mock_get_url.return_value = None
        
        with patch('data.download.DATA_DIR', temp_data_dir):
            from data.download import download_allen_data
            
            with pytest.raises(DownloadError, match="DATASET_URL not configured"):
                download_allen_data()

class TestMain:
    """Test main function entry point."""

    @patch('data.download.download_allen_data')
    @patch('data.download.logger')
    def test_main_success(self, mock_logger, mock_download):
        """Test successful main execution."""
        mock_path1 = MagicMock()
        mock_path1.exists.return_value = True
        mock_path2 = MagicMock()
        mock_path2.exists.return_value = True
        
        mock_download.return_value = (mock_path1, mock_path2)
        
        from data.download import main
        result = main()
        
        assert result == 0
        mock_download.assert_called_once()

    @patch('data.download.download_allen_data')
    @patch('data.download.logger')
    def test_main_download_error(self, mock_logger, mock_download):
        """Test main execution when download fails."""
        mock_download.side_effect = DownloadError("Download failed")
        
        from data.download import main
        result = main()
        
        assert result == 1
        mock_logger.error.assert_called()
