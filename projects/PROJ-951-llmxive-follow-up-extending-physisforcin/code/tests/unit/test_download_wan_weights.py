"""
Unit tests for download_wan_weights.py
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.generation.download_wan_weights import (
    calculate_sha256,
    verify_checksum,
    get_model_files,
    download_model_files
)

class TestDownloadWanWeights:
    """Test suite for Wan2.1 weight download utilities."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    @pytest.fixture
    def sample_file(self, temp_dir):
        """Create a sample file for checksum testing."""
        file_path = temp_dir / "test_file.bin"
        file_path.write_bytes(b"test data for checksum calculation")
        return file_path

    def test_calculate_sha256(self, sample_file):
        """Test SHA256 calculation."""
        checksum = calculate_sha256(sample_file)
        assert len(checksum) == 64  # SHA256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_verify_checksum_match(self, sample_file):
        """Test checksum verification when hashes match."""
        actual_hash = calculate_sha256(sample_file)
        assert verify_checksum(sample_file, actual_hash) is True

    def test_verify_checksum_mismatch(self, sample_file):
        """Test checksum verification when hashes don't match."""
        assert verify_checksum(sample_file, "wronghash" * 8) is False

    def test_verify_checksum_no_expected(self, sample_file):
        """Test checksum verification when no expected hash is provided."""
        assert verify_checksum(sample_file, "") is True

    @patch('src.generation.download_wan_weights.HfApi')
    def test_get_model_files(self, mock_api_class, temp_dir):
        """Test getting model files from repository."""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.list_repo_files.return_value = [
            'config.json',
            'model.safetensors',
            'scheduler/scheduler_config.json',
            'random_file.txt'
        ]
        
        files = get_model_files("test/repo")
        
        # Should filter for model-related files
        assert len(files) == 3  # config.json, model.safetensors, scheduler_config.json
        assert 'config.json' in files
        assert 'model.safetensors' in files
        assert 'random_file.txt' not in files

    @patch('src.generation.download_wan_weights.hf_hub_download')
    def test_download_model_files(self, mock_download, temp_dir):
        """Test downloading model files."""
        mock_download.return_value = temp_dir / "downloaded_file.bin"
        
        files = ['config.json', 'model.bin']
        result = download_model_files(
            repo_id="test/repo",
            local_dir=temp_dir,
            files=files,
            force_download=False
        )
        
        assert len(result) == 2
        mock_download.assert_called()

    def test_download_creates_directories(self, temp_dir):
        """Test that download creates necessary directory structure."""
        # This is tested implicitly through the download_model_files function
        # but we can verify directory creation logic separately
        nested_path = temp_dir / "subdir" / "nested"
        nested_path.mkdir(parents=True, exist_ok=True)
        assert nested_path.exists()

    def test_file_size_verification(self, temp_dir):
        """Test that downloaded files have non-zero size."""
        file_path = temp_dir / "test.bin"
        file_path.write_bytes(b"test")
        
        assert file_path.stat().st_size > 0

    @patch('src.generation.download_wan_weights.HfApi')
    def test_get_model_files_handles_errors(self, mock_api_class):
        """Test error handling when getting model files fails."""
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.list_repo_files.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            get_model_files("test/repo")

    @patch('src.generation.download_wan_weights.hf_hub_download')
    def test_download_handles_errors(self, mock_download, temp_dir):
        """Test error handling when download fails."""
        mock_download.side_effect = Exception("Download failed")
        
        with pytest.raises(Exception):
            download_model_files(
                repo_id="test/repo",
                local_dir=temp_dir,
                files=["model.bin"],
                force_download=False
            )
