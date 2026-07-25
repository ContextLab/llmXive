"""
Unit tests for memory monitoring utilities.
"""
import os
import sys
import time
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.memory_monitor import (
    MemoryMonitor,
    memory_limit_context,
    enforce_memory_limit,
    DEFAULT_MEMORY_LIMIT_GB
)

class TestMemoryMonitor:
    """Test cases for MemoryMonitor class."""

    def test_init_default_limit(self):
        """Test initialization with default limit."""
        monitor = MemoryMonitor()
        assert monitor.limit_gb == DEFAULT_MEMORY_LIMIT_GB
        assert monitor.limit_bytes == DEFAULT_MEMORY_LIMIT_GB * 1024**3
        assert monitor.peak_usage_gb == 0.0
        assert len(monitor.usage_history) == 0

    def test_init_custom_limit(self):
        """Test initialization with custom limit."""
        custom_limit = 4.0
        monitor = MemoryMonitor(limit_gb=custom_limit)
        assert monitor.limit_gb == custom_limit
        assert monitor.limit_bytes == custom_limit * 1024**3

    def test_get_current_usage_gb(self):
        """Test getting current memory usage."""
        monitor = MemoryMonitor()
        usage = monitor.get_current_usage_gb()
        
        # Should be a positive number
        assert isinstance(usage, float)
        assert usage > 0
        # Should be reasonable (less than 100GB for a test process)
        assert usage < 100.0

    def test_check_limit_within(self):
        """Test check_limit when within limit."""
        monitor = MemoryMonitor(limit_gb=100.0)  # Very high limit
        # Current usage should be well within 100GB
        assert monitor.check_limit() is True

    def test_check_limit_exceeded(self):
        """Test check_limit when exceeding limit."""
        # Create a monitor with a very low limit
        monitor = MemoryMonitor(limit_gb=0.0001)  # 0.1MB
        # Current usage should definitely exceed this
        assert monitor.check_limit() is False

    def test_force_gc(self):
        """Test force garbage collection."""
        monitor = MemoryMonitor()
        usage_before = monitor.get_current_usage_gb()
        usage_after = monitor.force_gc()
        
        # Usage after GC should be <= usage before
        assert usage_after <= usage_before

    def test_start_and_stop_monitoring(self):
        """Test starting and stopping background monitoring."""
        monitor = MemoryMonitor()
        
        # Start monitoring
        monitor.start_monitoring(interval=0.1)
        assert monitor._monitor_thread is not None
        assert monitor._monitor_thread.is_alive()
        
        # Wait a bit for some samples
        time.sleep(0.3)
        
        # Should have collected some history
        assert len(monitor.usage_history) > 0
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor._monitor_thread.is_alive()

    def test_get_statistics(self):
        """Test statistics retrieval."""
        monitor = MemoryMonitor(limit_gb=8.0)
        monitor.start_monitoring(interval=0.1)
        time.sleep(0.2)
        monitor.stop_monitoring()
        
        stats = monitor.get_statistics()
        
        assert 'current_gb' in stats
        assert 'peak_gb' in stats
        assert 'limit_gb' in stats
        assert 'samples' in stats
        
        assert stats['limit_gb'] == 8.0
        assert stats['samples'] > 0
        assert stats['current_gb'] > 0

    def test_save_report(self):
        """Test saving memory report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, 'test_report.txt')
            
            monitor = MemoryMonitor()
            monitor.start_monitoring(interval=0.1)
            time.sleep(0.2)
            monitor.stop_monitoring()
            
            monitor.save_report(path=report_path)
            
            assert os.path.exists(report_path)
            
            with open(report_path, 'r') as f:
                content = f.read()
            
            assert 'Memory Monitor Report' in content
            assert 'Limit:' in content
            assert 'Current Usage:' in content
            assert 'Peak Usage:' in content

class TestMemoryLimitContext:
    """Test cases for memory_limit_context context manager."""

    def test_context_manager_success(self):
        """Test context manager when limit is not exceeded."""
        with memory_limit_context(limit_gb=100.0) as monitor:
            # Should be able to access monitor
            assert monitor is not None
            assert isinstance(monitor, MemoryMonitor)
            # Should complete without error
            time.sleep(0.1)

    def test_context_manager_creates_report(self):
        """Test that context manager creates a report file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the results directory
            with patch('src.utils.memory_monitor._RESULTS_DIR', tmpdir):
                with memory_limit_context(limit_gb=100.0):
                    time.sleep(0.1)
                
                # Check that report was created
                report_path = os.path.join(tmpdir, 'memory_report.txt')
                assert os.path.exists(report_path)

class TestEnforceMemoryLimit:
    """Test cases for enforce_memory_limit decorator."""

    def test_decorator_success(self):
        """Test decorator when limit is not exceeded."""
        @enforce_memory_limit(limit_gb=100.0, check_interval=0.1)
        def simple_function():
            time.sleep(0.1)
            return "success"
        
        result = simple_function()
        assert result == "success"

    def test_decorator_report_created(self):
        """Test that decorator creates a report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.utils.memory_monitor._RESULTS_DIR', tmpdir):
                @enforce_memory_limit(limit_gb=100.0, check_interval=0.1)
                def test_func():
                    time.sleep(0.1)
                    return "done"
                
                test_func()
                
                report_path = os.path.join(tmpdir, 'memory_report.txt')
                assert os.path.exists(report_path)

@pytest.fixture
def temp_monitor():
    """Fixture providing a MemoryMonitor instance."""
    monitor = MemoryMonitor(limit_gb=8.0)
    yield monitor
    monitor.stop_monitoring()

def test_monitor_history_accumulation(temp_monitor):
    """Test that history accumulates during monitoring."""
    temp_monitor.start_monitoring(interval=0.05)
    time.sleep(0.2)
    temp_monitor.stop_monitoring()
    
    assert len(temp_monitor.usage_history) >= 3

def test_peak_tracking(temp_monitor):
    """Test that peak usage is tracked correctly."""
    temp_monitor.start_monitoring(interval=0.05)
    initial_usage = temp_monitor.get_current_usage_gb()
    time.sleep(0.2)
    temp_monitor.stop_monitoring()
    
    # Peak should be at least the initial usage
    assert temp_monitor.peak_usage_gb >= initial_usage

def test_limit_bytes_conversion():
    """Test that limit_bytes is correctly calculated."""
    limit_gb = 4.0
    monitor = MemoryMonitor(limit_gb=limit_gb)
    expected_bytes = limit_gb * (1024 ** 3)
    assert monitor.limit_bytes == expected_bytes

if __name__ == '__main__':
    pytest.main([__file__, '-v'])