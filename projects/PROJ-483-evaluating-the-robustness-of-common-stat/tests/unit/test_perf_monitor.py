"""
Unit tests for performance monitoring functionality.
"""
import os
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from perf_monitor import (
    get_memory_usage_mb,
    log_performance_metrics,
    measure_execution
)

class TestMemoryUsage:
    def test_get_memory_usage_mb_returns_positive_float(self):
        """Test that memory usage is a positive float."""
        memory = get_memory_usage_mb()
        assert isinstance(memory, float)
        assert memory > 0

class TestLogPerformanceMetrics:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Ensure results directory exists
        Path("results").mkdir(exist_ok=True)
        # Clean up any existing log file
        log_path = Path("results/perf_log.json")
        if log_path.exists():
            log_path.unlink()
        yield
        # Cleanup after test
        if log_path.exists():
            log_path.unlink()

    def test_log_performance_metrics_creates_file(self):
        """Test that log_performance_metrics creates the output file."""
        start = time.time()
        time.sleep(0.01)  # Small delay to ensure non-zero time
        end = time.time()
        
        metrics = log_performance_metrics(
            task_id="test_task",
            start_time=start,
            end_time=end
        )
        
        assert Path("results/perf_log.json").exists()
        
        with open("results/perf_log.json", 'r') as f:
            logs = json.load(f)
        
        assert isinstance(logs, list)
        assert len(logs) == 1
        assert logs[0]["task_id"] == "test_task"

    def test_log_performance_metrics_includes_required_fields(self):
        """Test that all required fields are present in the log."""
        start = time.time()
        end = time.time()
        
        metrics = log_performance_metrics(
            task_id="test_task",
            start_time=start,
            end_time=end
        )
        
        required_fields = [
            "task_id", "timestamp", "execution_time_seconds",
            "memory_usage_mb", "python_version", "platform", "config"
        ]
        
        for field in required_fields:
            assert field in metrics

    def test_log_performance_metrics_appends_to_existing_log(self):
        """Test that new entries are appended to existing log file."""
        start1 = time.time()
        end1 = time.time()
        log_performance_metrics(
            task_id="task_1",
            start_time=start1,
            end_time=end1
        )
        
        start2 = time.time()
        end2 = time.time()
        log_performance_metrics(
            task_id="task_2",
            start_time=start2,
            end_time=end2
        )
        
        with open("results/perf_log.json", 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 2
        assert logs[0]["task_id"] == "task_1"
        assert logs[1]["task_id"] == "task_2"

    def test_log_performance_metrics_with_additional_metrics(self):
        """Test that additional metrics are included in the log."""
        start = time.time()
        end = time.time()
        
        additional = {
            "custom_field": "custom_value",
            "numeric_field": 42
        }
        
        metrics = log_performance_metrics(
            task_id="test_task",
            start_time=start,
            end_time=end,
            additional_metrics=additional
        )
        
        assert metrics["custom_field"] == "custom_value"
        assert metrics["numeric_field"] == 42

class TestMeasureExecution:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        Path("results").mkdir(exist_ok=True)
        log_path = Path("results/perf_log.json")
        if log_path.exists():
            log_path.unlink()
        yield
        if log_path.exists():
            log_path.unlink()

    def test_measure_execution_returns_function_result(self):
        """Test that measure_execution returns the function's result."""
        def dummy_func(x, y):
            return x + y
        
        result = measure_execution(
            task_id="test_task",
            func=dummy_func,
            x=5,
            y=3
        )
        
        assert result == 8

    def test_measure_execution_logs_metrics(self):
        """Test that measure_execution logs performance metrics."""
        def dummy_func():
            time.sleep(0.01)
            return "done"
        
        measure_execution(
            task_id="test_task",
            func=dummy_func
        )
        
        assert Path("results/perf_log.json").exists()
        
        with open("results/perf_log.json", 'r') as f:
            logs = json.load(f)
        
        assert len(logs) == 1
        assert logs[0]["task_id"] == "test_task"
        assert logs[0]["execution_time_seconds"] > 0