"""
Unit tests for profile_simulation.py
"""
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from profile_simulation import (
    get_memory_usage_mb,
    run_profiled_sweep,
    write_profile_report,
    DEFAULT_SAMPLE_PARAMS
)
from utils.exceptions import SimulationError


class TestGetMemoryUsage:
    def test_get_memory_usage_returns_positive(self):
        """Test that memory usage is a positive number."""
        mem = get_memory_usage_mb()
        assert mem >= 0, "Memory usage should be non-negative"

    def test_get_memory_usage_reasonable_range(self):
        """Test that memory usage is within reasonable bounds (0-100000 MB)."""
        mem = get_memory_usage_mb()
        assert 0 <= mem <= 100000, f"Memory usage {mem} MB seems unreasonable"


class TestRunProfiledSweep:
    @patch('profile_simulation.generate_correlated_data')
    @patch('profile_simulation.run_hypothesis_tests')
    def test_sweep_runs_with_mocked_data(self, mock_tests, mock_data):
        """Test that sweep runs successfully with mocked data generation."""
        # Setup mocks
        mock_data.return_value = np.random.randn(10, 100)
        mock_tests.return_value = np.random.rand(100)
        
        sample_params = [
            {"n": 10, "p": 100, "rho": 0.5, "iterations": 2}
        ]
        
        result = run_profiled_sweep(sample_params)
        
        assert "total_runtime_seconds" in result
        assert "iterations_profiled" in result
        assert result["iterations_profiled"] == 2
        assert result["status"] in ["passed", "failed"]

    @patch('profile_simulation.generate_correlated_data')
    @patch('profile_simulation.run_hypothesis_tests')
    def test_sweep_handles_high_dimensional_error(self, mock_tests, mock_data):
        """Test that sweep handles HighDimensionalInstabilityError gracefully."""
        from utils.exceptions import HighDimensionalInstabilityError
        
        # First call succeeds, second fails
        mock_data.side_effect = [
            np.random.randn(10, 100),
            HighDimensionalInstabilityError("Test error")
        ]
        mock_tests.return_value = np.random.rand(100)
        
        sample_params = [
            {"n": 10, "p": 100, "rho": 0.5, "iterations": 2}
        ]
        
        result = run_profiled_sweep(sample_params)
        
        # Should complete with fewer iterations than requested
        assert result["iterations_profiled"] < 2

    def test_sweep_with_default_params(self):
        """Test that sweep runs with default parameters."""
        # This test will actually run a tiny sweep, so we limit iterations
        # In real usage, this would be mocked, but for unit test we verify structure
        sample_params = [
            {"n": 5, "p": 20, "rho": 0.1, "iterations": 1}
        ]
        
        result = run_profiled_sweep(sample_params)
        
        assert "total_runtime_seconds" in result
        assert "estimated_total_runtime_seconds" in result
        assert "max_memory_mb" in result
        assert "parameters_used" in result
        assert "results_per_config" in result


class TestWriteProfileReport:
    def test_write_report_creates_file(self, tmp_path):
        """Test that report file is created."""
        report_data = {
            "total_runtime_seconds": 10.5,
            "status": "passed"
        }
        
        output_path = tmp_path / "test_report.json"
        
        with patch('profile_simulation.PROFILE_OUTPUT_PATH', output_path):
            write_profile_report(report_data)
        
        assert output_path.exists()
        
        with open(output_path) as f:
            loaded = json.load(f)
        
        assert loaded["total_runtime_seconds"] == 10.5
        assert loaded["status"] == "passed"

    def test_write_report_valid_json(self, tmp_path):
        """Test that written report is valid JSON."""
        report_data = {
            "nested": {"value": 42},
            "list": [1, 2, 3],
            "float": 3.14
        }
        
        output_path = tmp_path / "test_report.json"
        
        with patch('profile_simulation.PROFILE_OUTPUT_PATH', output_path):
            write_profile_report(report_data)
        
        with open(output_path) as f:
            # Should not raise
            loaded = json.load(f)
        
        assert loaded == report_data


class TestProfileReportStructure:
    def test_report_has_required_fields(self):
        """Test that report contains all required fields."""
        sample_params = [
            {"n": 5, "p": 10, "rho": 0.1, "iterations": 1}
        ]
        
        result = run_profiled_sweep(sample_params)
        
        required_fields = [
            "total_runtime_seconds",
            "iterations_profiled",
            "estimated_total_runtime_seconds",
            "estimated_total_runtime_hours",
            "max_memory_mb",
            "parameters_used",
            "results_per_config",
            "status",
            "profile_timestamp",
            "max_allowed_hours"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_status_is_valid(self):
        """Test that status is either 'passed' or 'failed'."""
        sample_params = [
            {"n": 5, "p": 10, "rho": 0.1, "iterations": 1}
        ]
        
        result = run_profiled_sweep(sample_params)
        
        assert result["status"] in ["passed", "failed"]

    def test_runtime_values_are_positive(self):
        """Test that runtime values are non-negative."""
        sample_params = [
            {"n": 5, "p": 10, "rho": 0.1, "iterations": 1}
        ]
        
        result = run_profiled_sweep(sample_params)
        
        assert result["total_runtime_seconds"] >= 0
        assert result["estimated_total_runtime_seconds"] >= 0
        assert result["max_memory_mb"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])