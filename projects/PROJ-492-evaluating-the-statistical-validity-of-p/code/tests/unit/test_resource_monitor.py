"""
Unit tests for resource_monitor.py module.

Tests resource monitoring functionality including:
- Memory and CPU usage detection
- ResourceMonitor class behavior
- Limit checking and error handling
- Log file generation
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.utils.resource_monitor import (
    get_memory_usage_gb,
    get_cpu_cores,
    ResourceMonitor,
    start_monitoring,
    stop_monitoring,
    write_resource_log,
    ERR_301,
    MAX_RAM_GB,
    MAX_CPU_CORES
)

from code.src.utils.logger import get_default_logger


class TestMemoryAndCpuFunctions:
    """Test basic memory and CPU usage functions."""
    
    def test_get_memory_usage_gb_returns_positive_value(self):
        """Memory usage should always be a positive number."""
        ram = get_memory_usage_gb()
        assert isinstance(ram, float)
        assert ram > 0
        assert ram < 100  # Reasonable upper bound
    
    def test_get_cpu_cores_returns_non_negative_value(self):
        """CPU usage should be non-negative."""
        cpu = get_cpu_cores()
        assert isinstance(cpu, float)
        assert cpu >= 0
    
    def test_memory_usage_changes_with_work(self):
        """Memory usage should change when doing work."""
        ram_before = get_memory_usage_gb()
        
        # Do some work
        data = [i * i for i in range(100000)]
        
        ram_after = get_memory_usage_gb()
        
        # Memory should be at least the same or slightly higher
        # (allowing for GC timing)
        assert ram_after >= ram_before * 0.9  # Allow small variance


class TestResourceMonitor:
    """Test ResourceMonitor class functionality."""
    
    @pytest.fixture
    def temp_output_path(self):
        """Create a temporary output path for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "resource_log.json"
    
    def test_monitor_initialization(self, temp_output_path):
        """Monitor should initialize with correct defaults."""
        monitor = ResourceMonitor(temp_output_path)
        
        assert monitor.max_ram_gb == MAX_RAM_GB
        assert monitor.max_cpu_cores == MAX_CPU_CORES
        assert monitor.peak_ram_gb == 0.0
        assert monitor.peak_cpu_cores == 0.0
        assert monitor._monitoring is False
    
    def test_monitor_start_and_stop(self, temp_output_path):
        """Monitor should start and stop cleanly."""
        monitor = ResourceMonitor(temp_output_path)
        
        monitor.start()
        assert monitor._monitoring is True
        assert monitor.start_time is not None
        
        time.sleep(0.5)  # Let it collect some samples
        
        monitor.stop()
        assert monitor._monitoring is False
        assert monitor.end_time is not None
    
    def test_monitor_collects_samples(self, temp_output_path):
        """Monitor should collect samples during execution."""
        monitor = ResourceMonitor(temp_output_path)
        
        monitor.start()
        time.sleep(1.5)  # Wait for at least one sample
        monitor.stop()
        
        assert len(monitor._samples) >= 1
        sample = monitor._samples[0]
        assert 'timestamp' in sample
        assert 'ram_gb' in sample
        assert 'cpu_cores' in sample
    
    def test_monitor_tracks_peak_values(self, temp_output_path):
        """Monitor should track peak memory and CPU."""
        monitor = ResourceMonitor(temp_output_path)
        
        monitor.start()
        time.sleep(1.0)
        monitor.stop()
        
        stats = monitor.get_stats()
        assert stats['peak_ram_gb'] > 0
        assert stats['peak_cpu_cores'] >= 0
    
    def test_monitor_writes_log(self, temp_output_path):
        """Monitor should write JSON log file."""
        monitor = ResourceMonitor(temp_output_path)
        
        monitor.start()
        time.sleep(0.5)
        monitor.stop()
        monitor.write_log()
        
        assert temp_output_path.exists()
        
        with open(temp_output_path, 'r') as f:
            data = json.load(f)
        
        assert 'generated_at' in data
        assert 'results' in data
        assert 'peak_ram_gb' in data['results']
        assert 'within_limits' in data['results']
    
    def test_monitor_within_limits(self, temp_output_path):
        """Monitor should report within limits for normal usage."""
        monitor = ResourceMonitor(
            temp_output_path,
            max_ram_gb=100.0,  # Very high limit
            max_cpu_cores=100.0
        )
        
        monitor.start()
        time.sleep(0.5)
        monitor.stop()
        
        stats = monitor.get_stats()
        assert stats['within_limits'] is True
    
    def test_monitor_exceeds_memory_limit(self, temp_output_path):
        """Monitor should detect memory limit breach."""
        # Set very low limit
        monitor = ResourceMonitor(
            temp_output_path,
            max_ram_gb=0.0001,  # 0.1 MB - essentially impossible
            max_cpu_cores=100.0
        )
        
        monitor.start()
        
        # Should raise MemoryError on next check
        with pytest.raises(MemoryError) as exc_info:
            time.sleep(1.5)  # Wait for check
            monitor.stop()
        
        assert ERR_301 in str(exc_info.value)
    
    def test_monitor_get_stats_format(self, temp_output_path):
        """Stats dictionary should have correct structure."""
        monitor = ResourceMonitor(temp_output_path)
        
        monitor.start()
        time.sleep(0.5)
        monitor.stop()
        
        stats = monitor.get_stats()
        
        required_keys = [
            'start_time', 'end_time', 'duration_seconds',
            'peak_ram_gb', 'peak_cpu_cores',
            'max_ram_gb_limit', 'max_cpu_cores_limit',
            'samples_count', 'within_limits'
        ]
        
        for key in required_keys:
            assert key in stats


class TestMonitoringFunctions:
    """Test global monitoring functions."""
    
    @pytest.fixture
    def temp_output_path(self):
        """Create a temporary output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "resource_log.json"
    
    def test_start_and_stop_monitoring(self, temp_output_path):
        """Global start/stop should work correctly."""
        monitor = start_monitoring(temp_output_path)
        assert monitor is not None
        
        time.sleep(0.5)
        
        stats = stop_monitoring()
        assert stats is not None
        assert 'peak_ram_gb' in stats
    
    def test_write_resource_log_without_monitoring(self, temp_output_path):
        """Should create log even without active monitoring."""
        stats = write_resource_log(temp_output_path)
        
        assert stats is not None
        assert temp_output_path.exists()
        
        with open(temp_output_path, 'r') as f:
            data = json.load(f)
        
        assert 'results' in data
        assert 'note' in data['pipeline_info']
        assert data['pipeline_info']['note'] == 'Monitoring was not active'

class TestIntegration:
    """Integration tests for resource monitoring."""
    
    @pytest.fixture
    def temp_output_path(self):
        """Create a temporary output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "resource_log.json"
    
    def test_full_monitoring_cycle(self, temp_output_path):
        """Test complete monitoring lifecycle."""
        # Start
        monitor = start_monitoring(
            temp_output_path,
            max_ram_gb=50.0,
            max_cpu_cores=50.0
        )
        
        # Do some work
        time.sleep(1.0)
        data = [i * i for i in range(50000)]
        time.sleep(0.5)
        
        # Stop and verify
        stats = stop_monitoring()
        
        assert stats['within_limits'] is True
        assert stats['duration_seconds'] >= 1.0
        assert stats['peak_ram_gb'] > 0
        
        # Verify log file
        assert temp_output_path.exists()
        with open(temp_output_path, 'r') as f:
            log_data = json.load(f)
        
        assert log_data['results']['within_limits'] is True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
