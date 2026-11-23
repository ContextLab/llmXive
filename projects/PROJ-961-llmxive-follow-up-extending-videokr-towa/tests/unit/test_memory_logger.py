"""
Unit tests for memory_logger.py.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.memory_logger import get_peak_memory_gb, log_memory_usage, MEMORY_LIMIT_GB


class TestGetPeakMemoryGb:
    """Tests for the get_peak_memory_gb function."""

    @patch('utils.memory_logger.HAS_RESOURCE', True)
    @patch('utils.memory_logger.HAS_PSUTIL', False)
    @patch('utils.memory_logger.sys.platform', 'linux')
    @patch('utils.memory_logger.resource')
    def test_linux_memory_calculation(self, mock_resource):
        """Test memory calculation on Linux (KB to GB)."""
        # Mock ru_maxrss to be 1000000 KB (approx 1GB)
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 1000000
        mock_resource.getrusage.return_value = mock_rusage

        result = get_peak_memory_gb()

        # 1000000 KB * 1024 = bytes / (1024^3) = 1000000 / 1024 / 1024 ~ 0.9536 GB
        expected = (1000000 * 1024) / (1024 ** 3)
        assert abs(result - expected) < 1e-6

    @patch('utils.memory_logger.HAS_RESOURCE', True)
    @patch('utils.memory_logger.HAS_PSUTIL', False)
    @patch('utils.memory_logger.sys.platform', 'darwin')
    @patch('utils.memory_logger.resource')
    def test_macos_memory_calculation(self, mock_resource):
        """Test memory calculation on macOS (bytes to GB)."""
        # Mock ru_maxrss to be 1073741824 bytes (1GB)
        mock_rusage = MagicMock()
        mock_rusage.ru_maxrss = 1073741824
        mock_resource.getrusage.return_value = mock_rusage

        result = get_peak_memory_gb()

        expected = 1.0
        assert abs(result - expected) < 1e-6

    @patch('utils.memory_logger.HAS_RESOURCE', False)
    @patch('utils.memory_logger.HAS_PSUTIL', True)
    @patch('utils.memory_logger.psutil')
    def test_psutil_fallback(self, mock_psutil):
        """Test fallback to psutil on non-Unix systems."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=1073741824) # 1GB
        mock_psutil.Process.return_value = mock_process

        # Should not raise, but log a warning
        with patch('utils.memory_logger.logger') as mock_logger:
            result = get_peak_memory_gb()

            assert result == 1.0
            mock_logger.warning.assert_called_once()

    @patch('utils.memory_logger.HAS_RESOURCE', False)
    @patch('utils.memory_logger.HAS_PSUTIL', False)
    def test_no_memory_module_raises(self):
        """Test that RuntimeError is raised if no memory module is available."""
        with pytest.raises(RuntimeError, match="Cannot measure memory usage"):
            get_peak_memory_gb()


class TestLogMemoryUsage:
    """Tests for the log_memory_usage function."""

    def test_log_memory_creates_file(self, tmp_path):
        """Test that log_memory_usage creates the output JSON file."""
        output_file = tmp_path / "memory_log.json"

        # Patch get_peak_memory_gb to return a known value
        with patch('utils.memory_logger.get_peak_memory_gb', return_value=2.5):
            result = log_memory_usage(str(output_file))

        assert output_file.exists()
        assert result["status"] == "success"
        assert result["peak_memory_gb"] == 2.5
        assert result["limit_exceeded"] is False

    def test_log_memory_exceeds_limit(self, tmp_path):
        """Test that limit_exceeded is True when memory > 7GB."""
        output_file = tmp_path / "memory_log.json"
        limit = 7.0

        with patch('utils.memory_logger.get_peak_memory_gb', return_value=8.5):
            result = log_memory_usage(str(output_file))

        assert result["limit_exceeded"] is True
        assert result["limit_gb"] == limit

    def test_log_memory_within_limit(self, tmp_path):
        """Test that limit_exceeded is False when memory < 7GB."""
        output_file = tmp_path / "memory_log.json"

        with patch('utils.memory_logger.get_peak_memory_gb', return_value=3.0):
            result = log_memory_usage(str(output_file))

        assert result["limit_exceeded"] is False

    def test_log_memory_error_handling(self, tmp_path):
        """Test error handling when memory measurement fails."""
        output_file = tmp_path / "memory_log.json"

        with patch('utils.memory_logger.get_peak_memory_gb', side_effect=RuntimeError("Test error")):
            result = log_memory_usage(str(output_file))

        assert result["status"] == "error"
        assert "Test error" in result["error_message"]
        assert result["limit_exceeded"] is False # Cannot determine

    def test_log_memory_writes_json(self, tmp_path):
        """Test that the output file is valid JSON."""
        output_file = tmp_path / "memory_log.json"

        with patch('utils.memory_logger.get_peak_memory_gb', return_value=1.0):
            log_memory_usage(str(output_file))

        with open(output_file, 'r') as f:
            data = json.load(f)

        assert "peak_memory_gb" in data
        assert "limit_exceeded" in data
        assert "limit_gb" in data