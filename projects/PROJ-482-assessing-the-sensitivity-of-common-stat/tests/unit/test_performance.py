"""
Tests for performance monitoring and optimization utilities.
"""
import pytest
import os
import json
import tempfile
from datetime import datetime
import numpy as np

from performance_monitor import (
    load_performance_log,
    save_performance_log,
    log_scenario_execution,
    validate_performance_target,
    generate_performance_report,
    estimate_total_runtime
)

class TestPerformanceMonitor:
    """Tests for performance monitoring functions."""
    
    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create a temporary log file path."""
        return str(tmp_path / "test_performance_log.json")
    
    def test_load_empty_log(self, temp_log_file):
        """Test loading a non-existent log file returns empty structure."""
        log_data = load_performance_log(temp_log_file)
        assert log_data["scenarios"] == []
        assert log_data["total_runtime"] == 0
        assert log_data["start_time"] is None
    
    def test_log_scenario_execution(self, temp_log_file):
        """Test logging a scenario execution."""
        # Log a completed scenario
        log_scenario_execution(
            scenario_id="test_scenario_1",
            runtime_seconds=10.5,
            status="completed",
            log_path=temp_log_file
        )
        
        # Load and verify
        log_data = load_performance_log(temp_log_file)
        assert len(log_data["scenarios"]) == 1
        assert log_data["scenarios"][0]["scenario_id"] == "test_scenario_1"
        assert log_data["scenarios"][0]["runtime_seconds"] == 10.5
        assert log_data["total_runtime"] == 10.5
        assert log_data["start_time"] is not None
    
    def test_log_failed_scenario(self, temp_log_file):
        """Test logging a failed scenario."""
        log_scenario_execution(
            scenario_id="test_scenario_fail",
            runtime_seconds=5.0,
            status="failed",
            error_msg="Test error",
            log_path=temp_log_file
        )
        
        log_data = load_performance_log(temp_log_file)
        assert len(log_data["scenarios"]) == 1
        assert log_data["scenarios"][0]["status"] == "failed"
        assert log_data["scenarios"][0]["error_msg"] == "Test error"
        # Failed scenarios should not add to total_runtime
        assert log_data["total_runtime"] == 0
    
    def test_validate_performance_target_met(self, temp_log_file):
        """Test validation when target is met."""
        result = validate_performance_target(
            total_runtime=1000,
            num_scenarios=10,
            target_seconds=3600
        )
        
        assert result["passed"] is True
        assert result["remaining_budget"] == 2600
        assert result["avg_time_per_scenario"] == 100
    
    def test_validate_performance_target_exceeded(self, temp_log_file):
        """Test validation when target is exceeded."""
        result = validate_performance_target(
            total_runtime=5000,
            num_scenarios=10,
            target_seconds=3600
        )
        
        assert result["passed"] is False
        assert result["remaining_budget"] < 0
        assert "exceeded" in result["recommendation"].lower()
    
    def test_generate_performance_report(self, temp_log_file):
        """Test generating a performance report."""
        # Log some scenarios
        for i in range(5):
            log_scenario_execution(
                scenario_id=f"scenario_{i}",
                runtime_seconds=100 + i * 10,
                status="completed",
                log_path=temp_log_file
            )
        
        report = generate_performance_report(temp_log_file)
        
        assert report["status"] == "success"
        assert report["summary"]["num_scenarios"] == 5
        assert report["summary"]["failed_scenarios"] == 0
        assert report["statistics"]["average_time_per_scenario"] == 120  # (100+110+120+130+140)/5
        assert os.path.exists("data/processed/performance_report.json")
    
    def test_estimate_total_runtime(self, temp_log_file):
        """Test runtime estimation from sample."""
        sample_runtimes = [100, 120, 110, 130, 105]
        total_scenarios = 100
        
        estimate = estimate_total_runtime(sample_runtimes, total_scenarios)
        
        assert estimate["status"] == "estimated"
        assert estimate["sample_size"] == 5
        # Expected: avg=113, total=11300
        assert abs(estimate["estimated_total_seconds"] - 11300) < 100
        assert "confidence_interval_95" in estimate
    
    def test_estimate_insufficient_data(self, temp_log_file):
        """Test estimation with no data."""
        estimate = estimate_total_runtime([], 100)
        assert estimate["status"] == "insufficient_data"
