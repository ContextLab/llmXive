"""
Tests for constraint monitoring utilities (T044).
"""
import json
import tempfile
import os
import time
from pathlib import Path
import pytest
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.constraint_monitor import ConstraintMonitor


class TestConstraintMonitor:
    """Tests for ConstraintMonitor class"""

    def test_monitor_initialization(self):
        """Test monitor initialization with default values"""
        monitor = ConstraintMonitor()
        assert monitor.max_runtime_seconds == 6 * 3600
        assert monitor.max_memory_mb == 6 * 1024
        assert monitor.peak_memory_mb == 0.0

    def test_monitor_initialization_custom_limits(self):
        """Test monitor initialization with custom limits"""
        monitor = ConstraintMonitor(max_runtime_seconds=3600, max_memory_mb=2048)
        assert monitor.max_runtime_seconds == 3600
        assert monitor.max_memory_mb == 2048

    def test_memory_measurement(self):
        """Test that memory measurement returns positive value"""
        monitor = ConstraintMonitor()
        memory = monitor._get_current_memory_mb()
        assert memory > 0
        assert memory < 10000  # Should be reasonable

    def test_constraint_checking_pass(self):
        """Test constraint checking when constraints are satisfied"""
        monitor = ConstraintMonitor()
        results = {
            'peak_memory_mb': 1000,
            'total_runtime_seconds': 1000,
            'max_runtime_seconds': 3600,
            'max_memory_mb': 2048
        }
        assert monitor.check_constraints(results) is True

    def test_constraint_checking_fail_runtime(self):
        """Test constraint checking when runtime is exceeded"""
        monitor = ConstraintMonitor()
        results = {
            'peak_memory_mb': 1000,
            'total_runtime_seconds': 4000,
            'max_runtime_seconds': 3600,
            'max_memory_mb': 2048
        }
        assert monitor.check_constraints(results) is False

    def test_constraint_checking_fail_memory(self):
        """Test constraint checking when memory is exceeded"""
        monitor = ConstraintMonitor()
        results = {
            'peak_memory_mb': 3000,
            'total_runtime_seconds': 1000,
            'max_runtime_seconds': 3600,
            'max_memory_mb': 2048
        }
        assert monitor.check_constraints(results) is False

    def test_results_saving(self):
        """Test saving results to file"""
        monitor = ConstraintMonitor()
        results = {
            'peak_memory_mb': 1000,
            'total_runtime_seconds': 1000,
            'success': True
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            monitor.save_results(results, temp_path)
            assert os.path.exists(temp_path)

            with open(temp_path, 'r') as f:
                loaded = json.load(f)

            assert loaded == results
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_monitor_start_stop(self):
        """Test starting and stopping the monitor"""
        monitor = ConstraintMonitor()
        results_file = '/tmp/test_monitor.json'

        try:
            monitor.start(results_file)
            time.sleep(0.5)
            results = monitor.stop()

            assert 'peak_memory_mb' in results
            assert 'total_runtime_seconds' in results
            assert results['total_runtime_seconds'] >= 0
        finally:
            if os.path.exists(results_file):
                os.unlink(results_file)

    def test_monitor_thread_cleanup(self):
        """Test that monitor thread is properly cleaned up"""
        monitor = ConstraintMonitor()
        results_file = '/tmp/test_monitor_cleanup.json'

        try:
            monitor.start(results_file)
            time.sleep(0.2)
            results = monitor.stop()

            # Thread should be stopped
            assert monitor.monitoring_thread is None or not monitor.monitoring_thread.is_alive()
        finally:
            if os.path.exists(results_file):
                os.unlink(results_file)

    def test_peak_memory_tracking(self):
        """Test that peak memory is properly tracked"""
        monitor = ConstraintMonitor()
        results_file = '/tmp/test_peak_memory.json'

        try:
            monitor.start(results_file)
            # Simulate some work that might increase memory
            _ = [i for i in range(10000)]
            time.sleep(0.3)
            results = monitor.stop()

            assert results['peak_memory_mb'] > 0
        finally:
            if os.path.exists(results_file):
                os.unlink(results_file)

    def test_ci_environment_compatibility(self):
        """Test that monitor works in CI-like environment"""
        monitor = ConstraintMonitor()
        results_file = '/tmp/ci_test.json'

        try:
            monitor.start(results_file)
            time.sleep(0.1)
            results = monitor.stop()

            # Should work without errors
            assert 'peak_memory_mb' in results
            assert 'total_runtime_seconds' in results
        finally:
            if os.path.exists(results_file):
                os.unlink(results_file)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])