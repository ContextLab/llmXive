"""
Unit tests for the runtime monitoring utilities.
"""
import os
import time
import tempfile
import yaml
from pathlib import Path
import pytest
from datetime import datetime, timezone

from src.utils.runtime_monitor import (
    RuntimeMonitor,
    get_monitor,
    measure_total_benchmark_time,
    measure_per_task_time,
    TOTAL_BENCHMARK_LIMIT_SECONDS,
    PER_TASK_LIMIT_SECONDS
)


class TestRuntimeMonitor:
    """Tests for the RuntimeMonitor class."""

    def test_init_creates_output_directory(self):
        """Test that __init__ creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "metrics.yaml"
            monitor = RuntimeMonitor(output_path=output_path)
            assert output_path.parent.exists()

    def test_start_and_stop_benchmark(self):
        """Test starting and stopping the benchmark timer."""
        monitor = RuntimeMonitor()
        monitor.start_benchmark()
        time.sleep(0.05)  # Small delay
        monitor.stop_benchmark()
        
        total_time = monitor.measure_total_benchmark_time()
        assert total_time is not None
        assert total_time >= 0.05

    def test_start_without_stop_returns_none(self):
        """Test that measure_total_benchmark_time returns None if not stopped."""
        monitor = RuntimeMonitor()
        monitor.start_benchmark()
        assert monitor.measure_total_benchmark_time() is None

    def test_measure_task_context_manager(self):
        """Test the measure_task context manager."""
        monitor = RuntimeMonitor()
        
        with monitor.measure_task("test_task"):
            time.sleep(0.1)
        
        times = monitor.measure_per_task_time("test_task")
        assert len(times) == 1
        assert times[0] >= 0.1

    def test_multiple_task_measurements(self):
        """Test measuring multiple tasks."""
        monitor = RuntimeMonitor()
        
        with monitor.measure_task("task1"):
            time.sleep(0.05)
        
        with monitor.measure_task("task2"):
            time.sleep(0.05)
        
        with monitor.measure_task("task1"):  # Second run
            time.sleep(0.05)
        
        assert len(monitor.measure_per_task_time("task1")) == 2
        assert len(monitor.measure_per_task_time("task2")) == 1

    def test_verify_runtime_constraints_pass(self):
        """Test verification when constraints are met."""
        monitor = RuntimeMonitor()
        monitor.start_benchmark()
        
        with monitor.measure_task("quick_task"):
            time.sleep(0.01)
        
        monitor.stop_benchmark()
        
        results = monitor.verify_runtime_constraints()
        assert results["total_benchmark"]["passed"] is True
        assert results["per_task"]["passed"] is True
        assert len(results["per_task"]["violations"]) == 0

    def test_verify_runtime_constraints_total_fail(self):
        """Test verification when total benchmark time exceeds limit."""
        # Create a mock monitor that reports a very long time
        monitor = RuntimeMonitor()
        monitor.start_time = time.time() - (TOTAL_BENCHMARK_LIMIT_SECONDS + 100)
        monitor.end_time = time.time()
        
        results = monitor.verify_runtime_constraints()
        assert results["total_benchmark"]["passed"] is False
        assert "Exceeded limit" in results["total_benchmark"]["reason"]

    def test_verify_runtime_constraints_task_fail(self):
        """Test verification when a task exceeds the per-task limit."""
        monitor = RuntimeMonitor()
        monitor.task_times["slow_task"] = [PER_TASK_LIMIT_SECONDS + 100]
        
        results = monitor.verify_runtime_constraints()
        assert results["per_task"]["passed"] is False
        assert len(results["per_task"]["violations"]) == 1
        assert results["per_task"]["violations"][0]["task_id"] == "slow_task"

    def test_save_metrics(self):
        """Test saving metrics to a YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.yaml"
            monitor = RuntimeMonitor(output_path=output_path)
            
            monitor.start_benchmark()
            with monitor.measure_task("test_task"):
                time.sleep(0.01)
            monitor.stop_benchmark()
            
            saved_path = monitor.save_metrics()
            
            assert saved_path.exists()
            with open(saved_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert "timestamp" in data
            assert "benchmark" in data
            assert "task_metrics" in data
            assert "verification" in data
            assert data["task_metrics"]["test_task"]["count"] == 1

    def test_reset(self):
        """Test resetting the monitor state."""
        monitor = RuntimeMonitor()
        
        monitor.start_benchmark()
        with monitor.measure_task("task1"):
            time.sleep(0.01)
        monitor.stop_benchmark()
        
        monitor.reset()
        
        assert monitor.start_time is None
        assert monitor.end_time is None
        assert len(monitor.get_all_task_times()) == 0

    def test_get_all_task_times(self):
        """Test retrieving all task times."""
        monitor = RuntimeMonitor()
        
        with monitor.measure_task("a"):
            time.sleep(0.01)
        with monitor.measure_task("b"):
            time.sleep(0.01)
        
        all_times = monitor.get_all_task_times()
        assert "a" in all_times
        assert "b" in all_times


class TestGlobalMonitorFunctions:
    """Tests for the global monitor convenience functions."""

    def test_get_monitor_singleton(self):
        """Test that get_monitor returns the same instance."""
        monitor1 = get_monitor()
        monitor2 = get_monitor()
        assert monitor1 is monitor2

    def test_measure_total_benchmark_time_function(self):
        """Test the global measure_total_benchmark_time function."""
        monitor = get_monitor()
        monitor.reset()  # Ensure clean state
        
        # Before start
        assert measure_total_benchmark_time() is None
        
        monitor.start_benchmark()
        time.sleep(0.01)
        monitor.stop_benchmark()
        
        assert measure_total_benchmark_time() is not None
        assert measure_total_benchmark_time() >= 0.01

    def test_measure_per_task_time_function(self):
        """Test the global measure_per_task_time function."""
        monitor = get_monitor()
        monitor.reset()
        
        with monitor.measure_task("global_task"):
            time.sleep(0.01)
        
        times = measure_per_task_time("global_task")
        assert len(times) == 1
        assert times[0] >= 0.01

    def test_convenience_functions_use_same_instance(self):
        """Test that convenience functions use the global monitor instance."""
        monitor = get_monitor()
        monitor.reset()
        
        monitor.start_benchmark()
        with monitor.measure_task("convenience_test"):
            time.sleep(0.01)
        monitor.stop_benchmark()
        
        # Use convenience functions
        total = measure_total_benchmark_time()
        task_times = measure_per_task_time("convenience_test")
        
        assert total is not None
        assert len(task_times) == 1
        assert task_times[0] >= 0.01

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
