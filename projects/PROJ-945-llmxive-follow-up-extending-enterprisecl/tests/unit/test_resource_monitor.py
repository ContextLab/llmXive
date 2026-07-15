"""
Unit tests for resource_monitor.py
"""
import os
import json
import tempfile
import time
from pathlib import Path

import pytest

from src.utils.resource_monitor import ResourceMonitor


class TestResourceMonitor:
    """Tests for ResourceMonitor class."""
    
    def test_init_creates_log_directory(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "subdir", "log.json")
            monitor = ResourceMonitor(log_path=log_path)
            assert Path(log_path).parent.exists()
    
    def test_init_creates_empty_log_file(self):
        """Test that log file is created and initialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "log.json")
            monitor = ResourceMonitor(log_path=log_path)
            assert Path(log_path).exists()
            with open(log_path, 'r') as f:
                data = json.load(f)
            assert data == []
    
    def test_snapshot_records_data(self):
        """Test that snapshot records timestamp, elapsed, and RSS."""
        monitor = ResourceMonitor()
        snapshot = monitor.snapshot(label="test")
        
        assert 'timestamp' in snapshot
        assert 'elapsed_seconds' in snapshot
        assert 'rss_bytes' in snapshot
        assert 'rss_mb' in snapshot
        assert snapshot['label'] == 'test'
        assert snapshot['rss_bytes'] > 0
        assert snapshot['rss_mb'] > 0
    
    def test_multiple_snapshots(self):
        """Test that multiple snapshots are recorded."""
        monitor = ResourceMonitor()
        monitor.snapshot(label="first")
        time.sleep(0.1)
        monitor.snapshot(label="second")
        
        assert len(monitor.snapshots) == 2
        assert monitor.snapshots[0]['label'] == 'first'
        assert monitor.snapshots[1]['label'] == 'second'
        assert monitor.snapshots[1]['elapsed_seconds'] > monitor.snapshots[0]['elapsed_seconds']
    
    def test_peak_rss(self):
        """Test that peak RSS is correctly tracked."""
        monitor = ResourceMonitor()
        monitor.snapshot(label="low")
        # Force a snapshot (RSS might vary, but we just test the logic)
        monitor.snapshot(label="high")
        
        peak = monitor.get_peak_rss_bytes()
        assert peak > 0
        assert peak == monitor.get_peak_rss_mb() * 1024 * 1024
    
    def test_elapsed_time_increases(self):
        """Test that elapsed time increases between snapshots."""
        monitor = ResourceMonitor()
        t0 = monitor.get_elapsed_time()
        time.sleep(0.1)
        t1 = monitor.get_elapsed_time()
        assert t1 > t0
    
    def test_assert_memory_limit_passes(self):
        """Test that memory limit assertion passes when within limit."""
        monitor = ResourceMonitor()
        # Current usage should be well below 1000 MB
        assert monitor.assert_memory_limit(1000.0) is True
    
    def test_assert_memory_limit_fails(self):
        """Test that memory limit assertion fails when exceeded."""
        monitor = ResourceMonitor()
        # Set a very low limit that will definitely be exceeded
        with pytest.raises(RuntimeError, match="Memory limit exceeded"):
            monitor.assert_memory_limit(0.0001, raise_on_exceed=True)
    
    def test_assert_memory_limit_no_raise(self):
        """Test that memory limit check returns False without raising."""
        monitor = ResourceMonitor()
        result = monitor.assert_memory_limit(0.0001, raise_on_exceed=False)
        assert result is False
    
    def test_assert_time_limit_passes(self):
        """Test that time limit assertion passes when within limit."""
        monitor = ResourceMonitor()
        assert monitor.assert_time_limit(60.0) is True
    
    def test_assert_time_limit_fails(self):
        """Test that time limit assertion fails when exceeded."""
        monitor = ResourceMonitor()
        with pytest.raises(RuntimeError, match="Time limit exceeded"):
            # Set a negative limit to force immediate failure
            monitor.assert_time_limit(-1.0, raise_on_exceed=True)
    
    def test_summary(self):
        """Test that summary contains expected fields."""
        monitor = ResourceMonitor()
        monitor.snapshot(label="start")
        time.sleep(0.05)
        monitor.snapshot(label="end")
        
        summary = monitor.get_summary()
        
        assert 'start_time' in summary
        assert 'end_time' in summary
        assert 'duration_seconds' in summary
        assert 'peak_rss_mb' in summary
        assert 'snapshot_count' in summary
        assert summary['snapshot_count'] == 2
        assert summary['duration_seconds'] > 0
    
    def test_save_summary(self):
        """Test that summary is saved to a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "summary.json")
            monitor = ResourceMonitor()
            monitor.snapshot(label="test")
            monitor.save_summary(output_path)
            
            assert Path(output_path).exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert 'peak_rss_mb' in data
            assert 'snapshot_count' in data
    
    def test_log_file_appends(self):
        """Test that log file appends new snapshots."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "log.json")
            monitor = ResourceMonitor(log_path=log_path)
            
            monitor.snapshot(label="first")
            monitor.snapshot(label="second")
            
            with open(log_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['label'] == 'first'
            assert data[1]['label'] == 'second'
    
    def test_rss_bytes_to_mb_conversion(self):
        """Test that RSS conversion is correct."""
        monitor = ResourceMonitor()
        snapshot = monitor.snapshot()
        expected_mb = snapshot['rss_bytes'] / (1024 * 1024)
        assert abs(snapshot['rss_mb'] - expected_mb) < 1e-6