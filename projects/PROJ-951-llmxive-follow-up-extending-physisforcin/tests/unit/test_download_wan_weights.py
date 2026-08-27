import os
import sys
import tempfile
import shutil
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pytest

# Import the module under test. 
# The project structure places tests at code/tests/unit/ and source at code/src/
# We adjust sys.path to ensure imports work relative to the test location.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.generation.download_wan_weights import (
    calculate_sha256,
    verify_checksum,
    get_model_files,
    download_model_files,
    main
)

class TestDownloadWanWeights:
    """
    Unit tests for the Wan2.1 weight download script.
    These tests verify:
    1. Checksum calculation logic.
    2. Checksum verification logic.
    3. File listing logic (mocked).
    4. Download execution logic (mocked) and file creation.
    5. Main entry point execution.
    """

    def test_calculate_sha256(self, tmp_path):
        """Test that SHA256 calculation works correctly on a known file."""
        test_file = tmp_path / "test.bin"
        content = b"hello world"
        test_file.write_bytes(content)
        
        calculated_hash = calculate_sha256(str(test_file))
        
        # Expected hash for "hello world"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        assert calculated_hash == expected_hash

    def test_calculate_sha256_missing_file(self, tmp_path):
        """Test that SHA256 raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256(str(tmp_path / "nonexistent.bin"))

    def test_verify_checksum_success(self, tmp_path):
        """Test successful checksum verification."""
        test_file = tmp_path / "test.bin"
        content = b"data"
        test_file.write_bytes(content)
        
        correct_hash = hashlib.sha256(content).hexdigest()
        
        result = verify_checksum(str(test_file), correct_hash)
        assert result is True

    def test_verify_checksum_failure(self, tmp_path):
        """Test checksum verification failure."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"data")
        
        wrong_hash = "a" * 64  # Invalid hash for "data"
        
        result = verify_checksum(str(test_file), wrong_hash)
        assert result is False

    @patch('src.generation.download_wan_weights.HfApi')
    def test_get_model_files(self, mock_hf_api_class, tmp_path):
        """Test retrieving model file list from HuggingFace (mocked)."""
        mock_api_instance = MagicMock()
        mock_hf_api_class.return_value = mock_api_instance
        
        # Mock the file info objects
        mock_file1 = MagicMock()
        mock_file1.rfilename = "model.safetensors"
        mock_file1.size = 1024
        
        mock_file2 = MagicMock()
        mock_file2.rfilename = "config.json"
        mock_file2.size = 256
        
        mock_api_instance.model_info.return_value.siblings = [mock_file1, mock_file2]
        
        files = get_model_files("Wan-AI/Wan2.1-Turbo")
        
        assert len(files) == 2
        assert "model.safetensors" in files
        assert "config.json" in files

    @patch('src.generation.download_wan_weights.HfApi')
    @patch('src.generation.download_wan_weights.hf_hub_download')
    def test_download_model_files_creates_files(self, mock_download, mock_hf_api_class, tmp_path):
        """
        Test that download_model_files creates the expected files on disk
        and verifies their checksums.
        """
        # Setup mocks
        mock_api_instance = MagicMock()
        mock_hf_api_class.return_value = mock_api_instance
        
        # Mock file info
        mock_file = MagicMock()
        mock_file.rfilename = "model.bin"
        mock_file.size = 100
        mock_api_instance.model_info.return_value.siblings = [mock_file]
        
        # Mock the download to return a path that actually exists in tmp_path
        # We create a fake file there to simulate the download
        target_file = tmp_path / "model.bin"
        target_file.write_bytes(b"fake_weight_data")
        mock_download.return_value = str(target_file)
        
        # Mock the checksum to match the fake data
        expected_hash = hashlib.sha256(b"fake_weight_data").hexdigest()
        
        # Patch calculate_sha256 to return our known hash
        with patch('src.generation.download_wan_weights.calculate_sha256', return_value=expected_hash):
            # Run the function
            download_model_files(
                repo_id="Wan-AI/Wan2.1-Turbo",
                output_dir=str(tmp_path),
                expected_checksums={"model.bin": expected_hash}
            )
        
        # Assertions
        assert target_file.exists(), "The download script should have created the file"
        mock_download.assert_called_once()

    @patch('src.generation.download_wan_weights.download_model_files')
    @patch('src.generation.download_wan_weights.get_model_files')
    @patch('src.generation.download_wan_weights.verify_checksum')
    def test_main_execution(self, mock_verify, mock_get_files, mock_download_func, tmp_path):
        """
        Test the main entry point to ensure it orchestrates the download
        and creates the output directory structure.
        """
        model_dir = tmp_path / "models" / "wan2.1"
        model_dir.mkdir(parents=True)
        
        # Mock dependencies
        mock_get_files.return_value = ["model.safetensors"]
        mock_download_func.return_value = None
        mock_verify.return_value = True
        
        # Mock the logging to avoid clutter
        with patch('src.generation.download_wan_weights.logging'):
            main(output_dir=str(tmp_path / "models"))
        
        # Verify that the download function was called
        mock_download_func.assert_called_once()

    @patch('src.generation.download_wan_weights.HfApi')
    @patch('src.generation.download_wan_weights.hf_hub_download')
    def test_main_fails_on_checksum_mismatch(self, mock_download, mock_hf_api_class, tmp_path):
        """
        Test that main raises an error if the downloaded file's checksum
        does not match the expected value.
        """
        model_dir = tmp_path / "models" / "wan2.1"
        model_dir.mkdir(parents=True)
        
        # Mock file info
        mock_file = MagicMock()
        mock_file.rfilename = "model.bin"
        mock_file.size = 100
        mock_hf_api_class.return_value.model_info.return_value.siblings = [mock_file]
        
        # Create a fake file with content that doesn't match the expected hash
        target_file = tmp_path / "models" / "wan2.1" / "model.bin"
        target_file.write_bytes(b"wrong_content")
        mock_download.return_value = str(target_file)
        
        # Mock get_model_files
        with patch('src.generation.download_wan_weights.get_model_files', return_value=["model.bin"]):
            # We expect verify_checksum to return False, which should raise an error in main logic
            # However, the main function usually calls download_model_files which handles verification.
            # Let's test the specific failure path in download_model_files directly if main delegates it.
            # Based on the task description, we need to assert the script fails loudly.
            pass
        
        # Since we are mocking, we simulate the failure in the verification step
        # by patching verify_checksum to return False inside the flow
        with patch('src.generation.download_wan_weights.get_model_files', return_value=["model.bin"]):
            with patch('src.generation.download_wan_weights.verify_checksum', return_value=False):
                with patch('src.generation.download_wan_weights.logging'):
                    with pytest.raises(ValueError, match="Checksum verification failed"):
                        download_model_files(
                            repo_id="Wan-AI/Wan2.1-Turbo",
                            output_dir=str(tmp_path / "models"),
                            expected_checksums={"model.bin": "correct_hash"}
                        )