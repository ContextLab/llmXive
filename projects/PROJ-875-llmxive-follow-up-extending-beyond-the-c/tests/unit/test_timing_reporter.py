"""
Unit tests for the timing_reporter module.

Tests verify the logic for calculating pass/fail status and report generation.
"""
import json
import os
import tempfile
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from timing_reporter import (
    calculate_pass_fail,
    generate_timing_report,
    MAX_EXECUTION_SECONDS,
    TARGET_N
)

class TestCalculatePassFail:
    def test_pass_all_criteria_met(self):
        """Test passing case: N=20 and time < 6 hours."""
        total_time = 10000  # ~2.7 hours
        n_completed = 20
        
        result = calculate_pass_fail(total_time, n_completed)
        
        assert result["passed"] is True
        assert len(result["reasons"]) == 0
        assert result["actual_seconds"] == total_time
        assert result["instances_completed"] == n_completed

    def test_fail_time_exceeded(self):
        """Test failing case: time > 6 hours."""
        total_time = MAX_EXECUTION_SECONDS + 1000
        n_completed = 20
        
        result = calculate_pass_fail(total_time, n_completed)
        
        assert result["passed"] is False
        assert any("exceeded limit" in r for r in result["reasons"])

    def test_fail_incomplete_instances(self):
        """Test failing case: N < 20."""
        total_time = 10000
        n_completed = 15
        
        result = calculate_pass_fail(total_time, n_completed)
        
        assert result["passed"] is False
        assert any("Expected 20 instances" in r for r in result["reasons"])

    def test_fail_both_criteria(self):
        """Test failing case: both time and instance count issues."""
        total_time = MAX_EXECUTION_SECONDS + 1000
        n_completed = 15
        
        result = calculate_pass_fail(total_time, n_completed)
        
        assert result["passed"] is False
        assert len(result["reasons"]) == 2

    def test_edge_case_exactly_6_hours(self):
        """Test boundary: exactly 6 hours should pass (strictly less than is not required, 
        but typically <= is acceptable. Based on 'completes in <6 hours', we treat >= as fail)."""
        # The requirement says "<6 hours", so exactly 6 hours (21600) should fail
        total_time = 21600
        n_completed = 20
        
        result = calculate_pass_fail(total_time, n_completed)
        
        assert result["passed"] is False
        assert any("exceeded limit" in r for r in result["reasons"])

class TestGenerateTimingReport:
    def test_report_structure(self):
        """Test that the generated report has all required fields."""
        benchmark_data = {
            "total_execution_time_seconds": 10000,
            "instances_completed": 20,
            "runs": [
                {"run_id": 1, "seed": 1, "duration_seconds": 500, "status": "success"},
                {"run_id": 2, "seed": 2, "duration_seconds": 450, "status": "success"}
            ]
        }
        
        report = generate_timing_report(benchmark_data)
        
        assert "report_id" in report
        assert report["report_id"] == "SC-004-TIMING-REPORT"
        assert "generated_at" in report
        assert "spec_reference" in report
        assert report["spec_reference"] == "SC-004"
        assert "execution_metrics" in report
        assert "evaluation" in report
        assert "run_details" in report

    def test_execution_metrics_calculation(self):
        """Test that execution metrics are calculated correctly."""
        benchmark_data = {
            "total_execution_time_seconds": 20000,
            "instances_completed": 20,
            "runs": []
        }
        
        report = generate_timing_report(benchmark_data)
        
        metrics = report["execution_metrics"]
        assert metrics["total_time_seconds"] == 20000
        assert metrics["instances_completed"] == 20
        assert metrics["instances_target"] == 20
        assert metrics["average_time_per_instance"] == 1000

    def test_run_details_extraction(self):
        """Test that run details are correctly extracted from benchmark data."""
        benchmark_data = {
            "total_execution_time_seconds": 1000,
            "instances_completed": 2,
            "runs": [
                {"run_id": 1, "seed": 5, "duration_seconds": 400, "status": "success"},
                {"run_id": 2, "seed": 10, "duration_seconds": 600, "status": "success"}
            ]
        }
        
        report = generate_timing_report(benchmark_data)
        
        assert len(report["run_details"]) == 2
        assert report["run_details"][0]["seed"] == 5
        assert report["run_details"][1]["seed"] == 10
        assert report["run_details"][0]["duration_seconds"] == 400

    def test_empty_runs_list(self):
        """Test handling of empty runs list."""
        benchmark_data = {
            "total_execution_time_seconds": 0,
            "instances_completed": 0,
            "runs": []
        }
        
        report = generate_timing_report(benchmark_data)
        
        assert report["execution_metrics"]["average_time_per_instance"] == 0
        assert len(report["run_details"]) == 0

class TestIntegration:
    def test_full_report_generation_and_validation(self):
        """Integration test: generate a report and validate its structure."""
        benchmark_data = {
            "total_execution_time_seconds": 15000,
            "instances_completed": 20,
            "runs": [
                {"run_id": i, "seed": i, "duration_seconds": 750, "status": "success"}
                for i in range(1, 21)
            ]
        }
        
        report = generate_timing_report(benchmark_data)
        
        # Verify top-level structure
        assert report["evaluation"]["passed"] is True
        assert report["execution_metrics"]["total_time_seconds"] == 15000
        assert report["execution_metrics"]["average_time_per_instance"] == 750
        assert len(report["run_details"]) == 20
        
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))
