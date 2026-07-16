"""
Unit tests for timing utilities.

Tests the timing infrastructure to ensure it correctly measures
execution time, checks budget constraints, and generates reports.
"""
import time
import pytest
from pathlib import Path
import json
import tempfile
import os

from timing import (
    TimingReport,
    timed_pipeline,
    check_budget_usage,
    write_timing_report,
    verify_pipeline_budget
)

class TestTimingReport:
    """Tests for the TimingReport data class."""
    
    def test_timing_report_creation(self):
        """Test basic TimingReport creation."""
        report = TimingReport(
            total_time_seconds=100.0,
            budget_seconds=7200.0,
            stages=[{"name": "test", "duration": 10.0}],
            status="completed"
        )
        
        assert report.total_time_seconds == 100.0
        assert report.budget_seconds == 7200.0
        assert report.status == "completed"
        assert len(report.stages) == 1
    
    def test_timing_report_to_dict(self):
        """Test TimingReport serialization to dictionary."""
        report = TimingReport(
            total_time_seconds=100.0,
            budget_seconds=7200.0,
            stages=[{"name": "test", "duration": 10.0}],
            status="completed",
            error=None,
            cpu_time_seconds=95.0,
            memory_peak_mb=512.0
        )
        
        report_dict = report.to_dict()
        
        assert report_dict["total_time_seconds"] == 100.0
        assert report_dict["budget_seconds"] == 7200.0
        assert report_dict["status"] == "completed"
        assert report_dict["cpu_time_seconds"] == 95.0
        assert report_dict["memory_peak_mb"] == 512.0

class TestCheckBudgetUsage:
    """Tests for budget usage checking."""
    
    def test_budget_ok(self):
        """Test when usage is within budget."""
        result = check_budget_usage(
            elapsed_time=3600.0,
            budget_seconds=7200.0,
            threshold_percent=80.0
        )
        
        assert result["status"] == "ok"
        assert result["usage_percent"] == 50.0
        assert result["remaining_seconds"] == 3600.0
    
    def test_budget_warning(self):
        """Test when usage exceeds warning threshold."""
        result = check_budget_usage(
            elapsed_time=6000.0,
            budget_seconds=7200.0,
            threshold_percent=80.0
        )
        
        assert result["status"] == "warning"
        assert result["usage_percent"] > 80.0
    
    def test_budget_exceeded(self):
        """Test when usage exceeds budget."""
        result = check_budget_usage(
            elapsed_time=8000.0,
            budget_seconds=7200.0,
            threshold_percent=80.0
        )
        
        assert result["status"] == "exceeded"
        assert result["usage_percent"] > 100.0

class TestVerifyPipelineBudget:
    """Tests for pipeline budget verification."""
    
    def test_within_budget(self):
        """Test verification when within budget."""
        report = TimingReport(
            total_time_seconds=3600.0,
            budget_seconds=7200.0,
            stages=[],
            status="completed"
        )
        
        assert verify_pipeline_budget(report) is True
    
    def test_exceeds_budget(self):
        """Test verification when exceeds budget."""
        report = TimingReport(
            total_time_seconds=8000.0,
            budget_seconds=7200.0,
            stages=[],
            status="exceeded"
        )
        
        assert verify_pipeline_budget(report) is False

class TestWriteTimingReport:
    """Tests for timing report file writing."""
    
    def test_write_report(self):
        """Test writing timing report to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "timing_report.json"
            
            report = TimingReport(
                total_time_seconds=100.0,
                budget_seconds=7200.0,
                stages=[{"name": "test", "duration": 10.0}],
                status="completed"
            )
            
            write_timing_report(report, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_time_seconds"] == 100.0
            assert data["status"] == "completed"

class TestTimedPipeline:
    """Tests for the timed_pipeline context manager."""
    
    def test_timed_pipeline(self):
        """Test timing a simple operation."""
        report_list = []
        
        with timed_pipeline("test_stage", report_list):
            time.sleep(0.1)
        
        assert len(report_list) == 1
        assert report_list[0]["name"] == "test_stage"
        assert report_list[0]["duration_seconds"] >= 0.1
        assert "cpu_seconds" in report_list[0]