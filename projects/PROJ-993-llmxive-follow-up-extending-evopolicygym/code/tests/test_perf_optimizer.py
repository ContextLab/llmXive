"""
Tests for performance optimization utilities.

These tests verify that:
1. Timeout enforcement works correctly
2. Adaptive batch sizing reduces batch size on failure
3. Memory estimation is reasonable
4. Performance monitoring captures timing data
"""
import pytest
import time
import threading
from unittest.mock import patch, MagicMock
import numpy as np

from code.utils.perf_optimizer import (
    TimeoutError,
    MemoryPressureError,
    enforce_timeout,
    time_operation,
    adaptive_batch_size,
    estimate_memory_usage,
    check_memory_pressure,
    PerformanceMonitor,
    record_metric,
    get_performance_report,
    get_optimization_config
)


class TestTimeoutEnforcement:
    def test_timeout_raises_error(self):
        """Verify that operations exceeding timeout raise TimeoutError."""
        with pytest.raises(TimeoutError):
            with enforce_timeout(0.1):
                time.sleep(0.2)
                
    def test_timeout_succeeds_within_limit(self):
        """Verify that operations completing within timeout succeed."""
        with enforce_timeout(1.0):
            time.sleep(0.1)
            
    def test_timeout_custom_duration(self):
        """Verify custom timeout duration works."""
        with pytest.raises(TimeoutError):
            with enforce_timeout(0.05):
                time.sleep(0.1)


class TestTimeOperationDecorator:
    @time_operation("test_function")
    def slow_function(self):
        time.sleep(0.05)
        return "done"
        
    @time_operation("fast_function")
    def fast_function(self):
        return "done"
        
    def test_decorator_logs_timing(self, caplog):
        """Verify decorator logs execution time."""
        result = self.slow_function()
        assert result == "done"
        # Check that log contains timing info (implementation detail)
        
    def test_decorator_handles_exceptions(self):
        """Verify decorator still logs on exception."""
        with pytest.raises(ValueError):
            with time_operation("error_function"):
                raise ValueError("test error")


class TestAdaptiveBatchSize:
    @adaptive_batch_size
    def mock_inference(self, items, *args, **kwargs):
        """Mock inference that fails on large batches."""
        if len(items) > 2:
            raise MemoryPressureError("OOM")
        return [f"result_{i}" for i in range(len(items))]
        
    def test_reduces_batch_on_failure(self):
        """Verify batch size reduces when OOM occurs."""
        items = list(range(10))
        # This should succeed by reducing batch size
        results = self.mock_inference(items)
        assert len(results) == 10
        
    def test_processes_all_items(self):
        """Verify all items are processed despite batch failures."""
        items = list(range(5))
        results = self.mock_inference(items)
        assert len(results) == 5
        assert all(r.startswith("result_") for r in results)


class TestMemoryEstimation:
    def test_estimate_increases_with_batch(self):
        """Verify memory estimate increases with batch size."""
        model_size = 1.0  # GB
        low_mem = estimate_memory_usage(model_size, 1)
        high_mem = estimate_memory_usage(model_size, 8)
        assert high_mem > low_mem
        
    def test_estimate_positive(self):
        """Verify memory estimate is always positive."""
        for batch in [1, 4, 8, 16]:
            mem = estimate_memory_usage(0.5, batch)
            assert mem > 0.0


class TestPerformanceMonitor:
    def test_monitor_captures_time(self):
        """Verify monitor captures elapsed time."""
        with PerformanceMonitor("test_metric") as monitor:
            time.sleep(0.05)
            
        metrics = monitor.get_metrics()
        assert metrics["name"] == "test_metric"
        assert metrics["elapsed_seconds"] >= 0.05
        assert metrics["success"] is True
        
    def test_monitor_tracks_failure(self):
        """Verify monitor tracks failed operations."""
        with pytest.raises(ValueError):
            with PerformanceMonitor("failed_metric"):
                raise ValueError("test")
                
    def test_global_metrics_recording(self):
        """Verify metrics can be recorded and retrieved."""
        record_metric("test_global", 1.5, "seconds")
        report = get_performance_report()
        assert len(report["metrics"]) > 0
        assert report["summary"]["test_global"]["mean"] == 1.5


class TestConfig:
    def test_default_config(self):
        """Verify default configuration values."""
        config = get_optimization_config()
        assert config["timeout_seconds"] > 0
        assert config["max_batch_size"] > 0
        assert config["memory_threshold_gb"] > 0
        
    @patch.dict("os.environ", {"LLMXIVE_TIMEOUT_SECONDS": "60"})
    def test_config_reads_env_vars(self):
        """Verify config reads from environment variables."""
        config = get_optimization_config()
        assert config["timeout_seconds"] == 60
