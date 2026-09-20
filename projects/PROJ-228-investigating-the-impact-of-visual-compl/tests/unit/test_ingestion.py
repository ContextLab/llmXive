"""
Unit tests for code/ingestion.py
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib
import subprocess

# Import the module under test
# We need to ensure the import path works. Assuming tests are run from project root.
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.ingestion import (
    calculate_sha256,
    check_memory_limit,
    download_file_with_wget,
    verify_checksum,
    handle_missing_frames
)

class TestIngestionUtils:
    """Tests for utility functions in ingestion.py"""

    def test_calculate_sha256(self, tmp_path):
        """Test SHA256 calculation on a known string."""
        test_file = tmp_path / "test.txt"
        content = b"test content"
        test_file.write_bytes(content)
        
        expected_hash = hashlib.sha256(content).hexdigest()
        actual_hash = calculate_sha256(test_file)
        
        assert actual_hash == expected_hash

    def test_check_memory_limit_normal(self, monkeypatch):
        """Test that check_memory_limit passes when under limit."""
        # Mock psutil to return low memory usage
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 1024  # 1GB
        
        with patch('code.ingestion.psutil.Process', return_value=mock_process):
            # Should not raise
            check_memory_limit()

    def test_check_memory_limit_exceeded(self, monkeypatch):
        """Test that check_memory_limit raises when over limit."""
        # Mock psutil to return high memory usage (> 6GB)
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 7 * (1024 ** 3)  # 7GB
        
        with patch('code.ingestion.psutil.Process', return_value=mock_process):
            with pytest.raises(MemoryError, match="Memory limit exceeded"):
                check_memory_limit()

    def test_download_file_with_wget_success(self, tmp_path):
        """Test wget download simulation."""
        # Mock subprocess.run to simulate success
        with patch('code.ingestion.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            dest = tmp_path / "test.txt"
            result = download_file_with_wget("http://example.com/test.txt", dest, "Test File")
            
            assert result is True
            mock_run.assert_called_once()

    def test_download_file_with_wget_failure(self, tmp_path):
        """Test wget download failure handling."""
        with patch('code.ingestion.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "wget")
            
            dest = tmp_path / "test.txt"
            result = download_file_with_wget("http://example.com/test.txt", dest, "Test File")
            
            assert result is False

    def test_verify_checksum_match(self, tmp_path):
        """Test checksum verification when match."""
        test_file = tmp_path / "test.txt"
        content = b"test data"
        test_file.write_bytes(content)
        
        checksum = hashlib.sha256(content).hexdigest()
        
        assert verify_checksum(test_file, checksum) is True

    def test_verify_checksum_mismatch(self, tmp_path):
        """Test checksum verification when mismatch."""
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"test data")
        
        assert verify_checksum(test_file, "wrong_checksum") is False

    def test_verify_checksum_missing_file(self, tmp_path):
        """Test checksum verification when file missing."""
        missing_file = tmp_path / "nonexistent.txt"
        
        assert verify_checksum(missing_file) is False

    def test_handle_missing_frames(self, tmp_path):
        """Test that handle_missing_frames runs without error."""
        # This function currently just logs, so it should not raise
        result = handle_missing_frames(tmp_path)
        assert result is None
