"""
Unit tests for performance benchmarking logic.
"""
import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from performance_benchmark import get_memory_usage_mb, run_benchmark, MAX_TIME_SECONDS, MAX_MEMORY_MB

class TestMemoryUsage:
    def test_get_memory_usage_mb_returns_positive_float(self):
        """Ensure memory usage function returns a positive number."""
        mem = get_memory_usage_mb()
        assert isinstance(mem, float)
        assert mem > 0

class TestBenchmarkLogic:
    @patch('performance_benchmark.load_catalog')
    @patch('performance_benchmark.resolve_model')
    @patch('performance_benchmark.generate_code')
    @patch('performance_benchmark.run_coverage_on_task')
    def test_dry_run_completes_quickly(self, mock_cov, mock_gen, mock_resolve, mock_load):
        """Test that dry run simulates tasks without actual heavy processing."""
        # Mock catalog
        mock_catalog = [
            {"task_id": "task_1", "prompt": "test", "human_solution": "pass", "test_suite": "pass"},
            {"task_id": "task_2", "prompt": "test", "human_solution": "pass", "test_suite": "pass"}
        ]
        mock_load.return_value = mock_catalog
        mock_resolve.return_value = "mock-model"
        mock_gen.return_value = "dummy_path.py"
        mock_cov.return_value = {"line_coverage": 100, "branch_coverage": "N/A"}

        # Run with very small limit
        results = run_benchmark(task_limit=2, dry_run=True)

        assert results["successful"] == 2
        assert results["total_time_seconds"] < 5.0  # Should be very fast in dry run
        assert results["failed"] == 0

    @patch('performance_benchmark.load_catalog')
    @patch('performance_benchmark.resolve_model')
    @patch('performance_benchmark.generate_code')
    @patch('performance_benchmark.run_coverage_on_task')
    def test_benchmark_handles_generation_failure(self, mock_cov, mock_gen, mock_resolve, mock_load):
        """Test that benchmark counts failed tasks correctly."""
        mock_catalog = [
            {"task_id": "task_1", "prompt": "test", "human_solution": "pass", "test_suite": "pass"},
            {"task_id": "task_2", "prompt": "test", "human_solution": "pass", "test_suite": "pass"}
        ]
        mock_load.return_value = mock_catalog
        mock_resolve.return_value = "mock-model"
        mock_gen.side_effect = [None, "dummy_path.py"]  # First fails, second succeeds
        mock_cov.return_value = {"line_coverage": 100, "branch_coverage": "N/A"}

        results = run_benchmark(task_limit=2, dry_run=False)

        assert results["successful"] == 1
        assert results["failed"] == 1
        assert len(results["errors"]) == 1

class TestConstraints:
    def test_max_time_constant_is_six_hours(self):
        """Verify the 6-hour constraint is correctly defined."""
        assert MAX_TIME_SECONDS == 6 * 3600

    def test_max_memory_constant_is_seven_gb(self):
        """Verify the 7GB RAM constraint is correctly defined."""
        assert MAX_MEMORY_MB == 7 * 1024
