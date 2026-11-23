"""
Unit tests for the Time Budgeting & Profiler module (T039e).
"""
import os
import sys
import json
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.profiler import (
    profile_function,
    check_time_budget,
    run_psi4_profiling_test,
    log_profile_results,
    TIME_BUDGET_SECONDS,
    OUTPUT_FILE
)


class TestProfileFunction:
    def test_profile_successful_function(self):
        """Test profiling a function that runs successfully."""
        def dummy_func():
            time.sleep(0.1)

        metrics = profile_function(dummy_func, batch_size=1)

        assert metrics["function_name"] == "dummy_func"
        assert metrics["batch_size"] == 1
        assert metrics["elapsed_seconds"] >= 0.1
        assert metrics["exception_occurred"] is None

    def test_profile_failing_function(self):
        """Test profiling a function that raises an exception."""
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            profile_function(failing_func, batch_size=1)


class TestCheckTimeBudget:
    def test_within_budget(self):
        """Test check when execution is within budget."""
        metrics = {
            "elapsed_seconds": 100,
            "exception_occurred": None
        }
        assert check_time_budget(metrics) is True

    def test_exceeds_budget(self):
        """Test check when execution exceeds budget."""
        metrics = {
            "elapsed_seconds": TIME_BUDGET_SECONDS + 100,
            "exception_occurred": None
        }
        assert check_time_budget(metrics) is False

    def test_exception_occurred(self):
        """Test check when an exception occurred."""
        metrics = {
            "elapsed_seconds": 10,
            "exception_occurred": "RuntimeError"
        }
        assert check_time_budget(metrics) is False


class TestLogProfileResults:
    @patch('utils.profiler.OUTPUT_FILE', Path("/tmp/test_runtime_log.json"))
    def test_creates_log_file(self, tmp_path):
        """Test that log_profile_results creates the file."""
        # Override the path for the test
        import utils.profiler as profiler_module
        original_file = profiler_module.OUTPUT_FILE
        test_file = tmp_path / "runtime_log.json"
        profiler_module.OUTPUT_FILE = test_file

        try:
            metrics = {"elapsed_seconds": 10, "exception_occurred": None}
            log_profile_results(metrics, timestamp="2023-01-01")

            assert test_file.exists()
            with open(test_file, 'r') as f:
                data = json.load(f)
                assert len(data) == 1
                assert data[0]["task"] == "T039e_psi4_profiling"
        finally:
            profiler_module.OUTPUT_FILE = original_file


class TestRunPsi4ProfilingTest:
    def test_returns_metrics(self):
        """Test that the profiling test returns expected metrics structure."""
        metrics = run_psi4_profiling_test(sample_size=1)

        assert "function_name" in metrics
        assert "elapsed_seconds" in metrics
        assert "batch_size" in metrics
        assert "within_budget" in metrics
        assert isinstance(metrics["elapsed_seconds"], (int, float))