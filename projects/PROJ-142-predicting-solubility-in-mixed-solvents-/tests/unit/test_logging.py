import json
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
import resource
import os

import pytest

# Import the function to test
# Assuming the file is at code/utils/logging.py and we are running from project root or code/
# We need to ensure the path is correct.
try:
    from utils.logging import monitor_resources
except ImportError:
    # Fallback for different execution contexts
    sys.path.insert(0, 'code')
    from utils.logging import monitor_resources

def test_monitor_resources_normal():
    """Test that monitor_resources logs ok status when limits are not exceeded."""
    # Mock resource.getrusage to return low values
    mock_usage = MagicMock()
    mock_usage.ru_maxrss = 1000  # ~1MB, well below 7GB
    
    # Mock os.statvfs to return low disk usage
    mock_st = MagicMock()
    mock_st.f_bavail = 1000000
    mock_st.f_frsize = 512
    mock_st.f_blocks = 10000000
    
    with patch('utils.logging.resource.getrusage', return_value=mock_usage), \
         patch('utils.logging.os.statvfs', return_value=mock_st), \
         patch('sys.stderr', new_callable=StringIO) as mock_stderr:
        
        monitor_resources(ram_limit_gb=7.0, disk_limit_gb=14.0)
        
        output = mock_stderr.getvalue()
        lines = output.strip().split('\n')
        
        # First line should be the JSON log
        json_line = lines[0]
        log_entry = json.loads(json_line)
        
        assert log_entry["status"] == "ok"
        assert "timestamp" in log_entry
        assert "ram_gb" in log_entry
        assert "disk_gb" in log_entry
        
        # Ensure no error message was printed
        assert "ERROR: Resource limit exceeded" not in output

def test_monitor_resources_critical_ram():
    """Test that monitor_resources exits with code 1 when RAM limit is exceeded."""
    # Mock resource.getrusage to return high RAM usage (e.g., 8GB)
    # 8GB in KB = 8 * 1024 * 1024
    mock_usage = MagicMock()
    mock_usage.ru_maxrss = 8 * 1024 * 1024
    
    mock_st = MagicMock()
    mock_st.f_bavail = 1000000
    mock_st.f_frsize = 512
    mock_st.f_blocks = 10000000

    with patch('utils.logging.resource.getrusage', return_value=mock_usage), \
         patch('utils.logging.os.statvfs', return_value=mock_st), \
         patch('sys.stderr', new_callable=StringIO) as mock_stderr, \
         patch('sys.exit') as mock_exit:
        
        monitor_resources(ram_limit_gb=7.0, disk_limit_gb=14.0)
        
        output = mock_stderr.getvalue()
        assert "ERROR: Resource limit exceeded" in output
        mock_exit.assert_called_once_with(1)

def test_monitor_resources_critical_disk():
    """Test that monitor_resources exits with code 1 when disk limit is exceeded."""
    mock_usage = MagicMock()
    mock_usage.ru_maxrss = 1000
    
    # Mock disk usage to be high (e.g., 15GB)
    # 15GB in bytes = 15 * 1024^3
    # total = used + free. Let's say used is 15GB.
    # We need to set total and free such that (total - free) > 15GB
    # Let total = 20GB, free = 4GB -> used = 16GB
    used_gb = 16.0
    free_gb = 4.0
    total_gb = 20.0
    
    block_size = 512
    total_blocks = int((total_gb * (1024**3)) / block_size)
    free_blocks = int((free_gb * (1024**3)) / block_size)
    
    mock_st = MagicMock()
    mock_st.f_bavail = free_blocks
    mock_st.f_frsize = block_size
    mock_st.f_blocks = total_blocks

    with patch('utils.logging.resource.getrusage', return_value=mock_usage), \
         patch('utils.logging.os.statvfs', return_value=mock_st), \
         patch('sys.stderr', new_callable=StringIO) as mock_stderr, \
         patch('sys.exit') as mock_exit:
        
        monitor_resources(ram_limit_gb=7.0, disk_limit_gb=14.0)
        
        output = mock_stderr.getvalue()
        assert "ERROR: Resource limit exceeded" in output
        mock_exit.assert_called_once_with(1)