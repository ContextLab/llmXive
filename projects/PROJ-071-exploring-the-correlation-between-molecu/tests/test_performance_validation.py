"""
Tests for T042: Performance validation module.

These tests verify that the performance validation script correctly:
1. Measures execution time
2. Compares against threshold
3. Generates proper output files
4. Handles errors appropriately
"""

import os
import sys
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.validate_performance import (
    validate_pipeline_performance,
    PERFORMANCE_THRESHOLD_SECONDS,
    OUTPUT_FILE
)

class TestPerformanceValidation:
    """Test suite for performance validation functionality."""

    @pytest.fixture
    def mock_pipeline_success(self):
        """Mock a successful pipeline execution."""
        return {
            "status": "success",
            "data_files": ["data/processed/merged_drugs.csv"],
            "analysis_results": "data/processed/analysis_results.json"
        }

    @pytest.fixture
    def mock_pipeline_failure(self):
        """Mock a failed pipeline execution."""
        return {
            "status": "error",
            "error": "Data availability gate failed: N < 30"
        }

    def test_execution_time_measurement(self, mock_pipeline_success):
        """Test that execution time is correctly measured."""
        with patch('code.validate_performance.run_pipeline', return_value=mock_pipeline_success):
            with patch('code.validate_performance.time.time') as mock_time:
                # Simulate start and end times
                mock_time.side_effect = [0, 10]  # 10 seconds elapsed
                
                results = validate_pipeline_performance()
                
                assert results["total_duration_seconds"] == 10.0
                assert results["execution_success"] is True

    def test_threshold_comparison_pass(self, mock_pipeline_success):
        """Test that execution below threshold passes validation."""
        with patch('code.validate_performance.run_pipeline', return_value=mock_pipeline_success):
            with patch('code.validate_performance.time.time') as mock_time:
                # Simulate execution time well below threshold
                mock_time.side_effect = [0, 50]  # 50 seconds elapsed
                
                results = validate_pipeline_performance()
                
                assert results["passed"] is True
                assert results["status"] == "PASS"
                assert results["threshold_met"] is True

    def test_threshold_comparison_fail(self, mock_pipeline_success):
        """Test that execution above threshold fails validation."""
        with patch('code.validate_performance.run_pipeline', return_value=mock_pipeline_success):
            with patch('code.validate_performance.time.time') as mock_time:
                # Simulate execution time above threshold
                mock_time.side_effect = [0, PERFORMANCE_THRESHOLD_SECONDS + 60]  # Above threshold
                
                results = validate_pipeline_performance()
                
                assert results["passed"] is False
                assert results["status"] == "FAIL"
                assert results["threshold_met"] is False

    def test_pipeline_failure_handling(self, mock_pipeline_failure):
        """Test that pipeline failures are correctly detected and reported."""
        with patch('code.validate_performance.run_pipeline', return_value=mock_pipeline_failure):
            with patch('code.validate_performance.time.time') as mock_time:
                mock_time.side_effect = [0, 30]  # 30 seconds elapsed
                
                results = validate_pipeline_performance()
                
                assert results["execution_success"] is False
                assert results["passed"] is False
                assert results["status"] == "FAIL"
                assert "Data availability gate failed" in results["error_message"]

    def test_output_file_generation(self, mock_pipeline_success):
        """Test that output file is correctly generated."""
        with patch('code.validate_performance.run_pipeline', return_value=mock_pipeline_success):
            with patch('code.validate_performance.time.time') as mock_time:
                mock_time.side_effect = [0, 10]
                
                results = validate_pipeline_performance()
                
                output_path = project_root / OUTPUT_FILE
                assert output_path.exists()
                
                # Verify JSON structure
                with open(output_path, 'r') as f:
                    saved_results = json.load(f)
                
                assert "timestamp" in saved_results
                assert "total_duration_seconds" in saved_results
                assert "passed" in saved_results
                assert "status" in saved_results
                assert saved_results["status"] == "PASS"

    def test_exception_handling(self):
        """Test that exceptions during pipeline execution are caught and reported."""
        with patch('code.validate_performance.run_pipeline', side_effect=Exception("Simulated pipeline error")):
            with patch('code.validate_performance.time.time') as mock_time:
                mock_time.side_effect = [0, 15]
                
                results = validate_pipeline_performance()
                
                assert results["execution_success"] is False
                assert results["passed"] is False
                assert "Simulated pipeline error" in results["error_message"]

    def test_threshold_configuration(self):
        """Test that threshold is correctly configured."""
        assert isinstance(PERFORMANCE_THRESHOLD_SECONDS, (int, float))
        assert PERFORMANCE_THRESHOLD_SECONDS > 0

    def test_result_structure_completeness(self, mock_pipeline_success):
        """Test that all required fields are present in results."""
        with patch('code.validate_performance.run_pipeline', return_value=mock_pipeline_success):
            with patch('code.validate_performance.time.time') as mock_time:
                mock_time.side_effect = [0, 10]
                
                results = validate_pipeline_performance()
                
                required_fields = [
                    "timestamp",
                    "execution_success",
                    "total_duration_seconds",
                    "threshold_seconds",
                    "passed",
                    "status",
                    "error_message",
                    "details"
                ]
                
                for field in required_fields:
                    assert field in results, f"Missing required field: {field}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
