import os
import sys
import time
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.memory_monitor import (
    MemoryMonitor,
    measure_memory,
    check_memory_limit,
    get_session_metrics,
    clear_session_metrics,
    should_batch_process
)
from utils.seeds import set_global_seed

# Set seed for reproducibility
set_global_seed(42)

def test_memory_monitor_init():
    """Test MemoryMonitor initialization."""
    monitor = MemoryMonitor()
    
    assert monitor is not None
    assert monitor.session_start is not None
    assert monitor.peak_memory == 0

def test_memory_monitor_measure():
    """Test memory measurement."""
    monitor = MemoryMonitor()
    
    # Perform some memory-intensive operation
    data = [i for i in range(100000)]
    
    with monitor.measure():
        _ = sum(data)
    
    assert monitor.peak_memory > 0

def test_measure_memory_decorator():
    """Test measure_memory decorator."""
    @measure_memory
    def test_function():
        data = [i for i in range(10000)]
        return sum(data)
    
    result = test_function()
    assert result > 0

def test_check_memory_limit():
    """Test memory limit checking."""
    # Test with a limit that should pass
    assert check_memory_limit(5.0, 10.0) == True
    
    # Test with a limit that should fail
    assert check_memory_limit(15.0, 10.0) == False

def test_get_session_metrics():
    """Test getting session metrics."""
    clear_session_metrics()
    
    monitor = MemoryMonitor()
    data = [i for i in range(10000)]
    
    with monitor.measure():
        _ = sum(data)
    
    metrics = get_session_metrics()
    
    assert metrics is not None
    assert 'peak_memory_gb' in metrics
    assert 'elapsed_time' in metrics

def test_clear_session_metrics():
    """Test clearing session metrics."""
    clear_session_metrics()
    
    metrics = get_session_metrics()
    assert metrics['peak_memory_gb'] == 0
    assert metrics['elapsed_time'] == 0

def test_should_batch_process():
    """Test batch processing decision."""
    # Should batch when memory is high
    assert should_batch_process(7.0, 6.0) == True
    
    # Should not batch when memory is low
    assert should_batch_process(4.0, 6.0) == False

def test_memory_monitor_context_manager():
    """Test MemoryMonitor as context manager."""
    with MemoryMonitor() as monitor:
        data = [i for i in range(100000)]
        _ = sum(data)
    
    assert monitor.peak_memory > 0
    assert monitor.elapsed_time > 0

def test_memory_monitor_with_mock():
    """Test memory monitoring with mocked memory usage."""
    with patch('utils.memory_monitor.psutil') as mock_psutil:
        # Mock memory info
        mock_process = MagicMock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
        mock_psutil.Process.return_value = mock_process
        
        monitor = MemoryMonitor()
        
        with monitor.measure():
            data = [i for i in range(10000)]
            _ = sum(data)
        
        assert monitor.peak_memory > 0
