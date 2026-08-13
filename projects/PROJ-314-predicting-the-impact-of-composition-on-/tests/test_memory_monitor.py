import os
import sys
import pytest
from unittest.mock import patch, MagicMock
import psutil

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from memory_monitor import get_memory_usage_gb, check_memory_limit, force_garbage_collection, validate_dataset_size, log_memory_usage

class TestMemoryMonitor:
    def test_get_memory_usage_gb_positive(self):
        """Test that get_memory_usage_gb returns a positive number."""
        usage = get_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0

    @patch('memory_monitor.psutil.Process')
    def test_check_memory_limit_exceeded(self, mock_process):
        """Test that MemoryError is raised when limit is exceeded."""
        # Mock memory info to return 10GB
        mock_process.return_value.memory_info.return_value.rss = 10 * (1024 ** 3)
        
        with pytest.raises(MemoryError):
            check_memory_limit(limit_gb=5.0)

    @patch('memory_monitor.psutil.Process')
    def test_check_memory_limit_ok(self, mock_process):
        """Test that check_memory_limit returns False when within limit."""
        # Mock memory info to return 2GB
        mock_process.return_value.memory_info.return_value.rss = 2 * (1024 ** 3)
        
        result = check_memory_limit(limit_gb=5.0)
        assert result is False

    def test_force_garbage_collection(self):
        """Test that force_garbage_collection runs without error."""
        result = force_garbage_collection()
        assert isinstance(result, int)
        assert result >= 0

    @patch('memory_monitor.Path')
    @patch('os.path.getsize')
    def test_validate_dataset_size_ok(self, mock_getsize, mock_path):
        """Test validate_dataset_size when file is within limit."""
        mock_getsize.return_value = 1024 * 1024 * 1024  # 1GB
        mock_path.return_value.exists.return_value = True
        
        result = validate_dataset_size("dummy_path.csv", max_size_gb=5.0)
        assert result is True

    @patch('memory_monitor.Path')
    @patch('os.path.getsize')
    def test_validate_dataset_size_too_large(self, mock_getsize, mock_path):
        """Test validate_dataset_size raises MemoryError when file is too large."""
        mock_getsize.return_value = 20 * (1024 ** 3)  # 20GB
        mock_path.return_value.exists.return_value = True
        
        with pytest.raises(MemoryError):
            validate_dataset_size("dummy_path.csv", max_size_gb=5.0)

    @patch('memory_monitor.Path')
    def test_validate_dataset_size_not_found(self, mock_path):
        """Test validate_dataset_size raises FileNotFoundError when file missing."""
        mock_path.return_value.exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            validate_dataset_size("dummy_path.csv", max_size_gb=5.0)

    @patch('memory_monitor.Path')
    def test_log_memory_usage_creates_file(self, mock_path):
        """Test that log_memory_usage creates the log file."""
        # Mock path to avoid actual file system interaction in test logic,
        # but we verify the call sequence.
        mock_path.return_value.parent.mkdir = MagicMock()
        
        with patch('builtins.open', MagicMock()) as mock_open:
            with patch('memory_monitor.get_memory_usage_gb', return_value=2.0):
                with patch('memory_monitor.get_int_config', return_value=6):
                    metrics = log_memory_usage(log_path="test_log.log")
                    
                    assert 'rss_gb' in metrics
                    assert metrics['status'] == 'OK'
                    mock_open.assert_called()