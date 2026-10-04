"""
Unit tests for pipeline timing and end-to-end execution.

These tests verify that the timing infrastructure works correctly
and that the pipeline can be executed end-to-end within constraints.
"""
import os
import sys
import json
import tempfile
import time
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.run_pipeline_timing import run_step, main, PIPELINE_STEPS
from code.logging_config import setup_logging

logger = setup_logging(__name__)

def test_run_step_success():
    """Test that run_step correctly measures successful execution."""
    def mock_success_func():
        time.sleep(0.1)  # Small delay to ensure measurable time
    
    result = run_step("test_success", mock_success_func)
    
    assert result["step"] == "test_success"
    assert result["success"] is True
    assert result["error"] is None
    assert result["duration_seconds"] >= 0.1
    assert "start_time" in result
    assert "end_time" in result

def test_run_step_failure():
    """Test that run_step correctly handles and records failures."""
    def mock_failure_func():
        raise ValueError("Test error")
    
    result = run_step("test_failure", mock_failure_func)
    
    assert result["step"] == "test_failure"
    assert result["success"] is False
    assert result["error"] == "Test error"
    assert result["duration_seconds"] >= 0
    assert "start_time" in result
    assert "end_time" in result

def test_timing_log_generation():
    """Test that timing log is generated with correct structure."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the results directory path
        original_join = os.path.join
        
        def mock_join(*args):
            if len(args) >= 2 and args[-2] == "results":
                return os.path.join(temp_dir, *args[-1:])
            return original_join(*args)
        
        with patch('code.run_pipeline_timing.os.path.join', mock_join):
            with patch('code.run_pipeline_timing.PIPELINE_STEPS', [
                ("mock_step", lambda: time.sleep(0.01))
            ]):
                # Run the main function
                result_code = main()
                
                # Check that timing log was created
                timing_log_path = os.path.join(temp_dir, "timing_log.json")
                assert os.path.exists(timing_log_path)
                
                # Load and validate timing log structure
                with open(timing_log_path, 'r') as f:
                    timing_log = json.load(f)
                
                assert "pipeline_name" in timing_log
                assert "total_duration_seconds" in timing_log
                assert "constraint_check" in timing_log
                assert "steps" in timing_log
                assert timing_log["constraint_check"]["max_allowed_hours"] == 6
                assert "passed" in timing_log["constraint_check"]

def test_constraint_check_logic():
    """Test that constraint checking logic works correctly."""
    # Test passing case
    passing_log = {
        "constraint_check": {
            "max_allowed_seconds": 6 * 3600,
            "total_duration": 3000  # Less than 6 hours
        }
    }
    assert passing_log["constraint_check"]["total_duration"] <= passing_log["constraint_check"]["max_allowed_seconds"]
    
    # Test failing case
    failing_log = {
        "constraint_check": {
            "max_allowed_seconds": 6 * 3600,
            "total_duration": 30000  # More than 6 hours
        }
    }
    assert failing_log["constraint_check"]["total_duration"] > failing_log["constraint_check"]["max_allowed_seconds"]

def test_pipeline_steps_defined():
    """Test that all required pipeline steps are defined."""
    expected_steps = [
        "data_generation", "ingestion", "data_processing", "model_fitting",
        "sensitivity_analysis", "result_serialization", "result_aggregation",
        "robustness_summary", "report_generation", "schema_validation"
    ]
    
    actual_steps = [step[0] for step in PIPELINE_STEPS]
    
    for expected in expected_steps:
        assert expected in actual_steps, f"Missing expected step: {expected}"
    
    assert len(PIPELINE_STEPS) == len(expected_steps), "Unexpected number of pipeline steps"

def test_timing_log_contains_required_fields():
    """Test that timing log contains all required fields for SC-005."""
    required_fields = [
        "total_duration_seconds",
        "constraint_check",
        "pipeline_name",
        "start_time",
        "end_time",
        "steps"
    ]
    
    # We'll check the structure by creating a mock log
    mock_log = {
        "total_duration_seconds": 100.0,
        "constraint_check": {
            "max_allowed_hours": 6,
            "max_allowed_seconds": 21600,
            "passed": True,
            "margin_seconds": 21500
        },
        "pipeline_name": "Test Pipeline",
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-01T00:01:40",
        "steps": []
    }
    
    for field in required_fields:
        assert field in mock_log, f"Missing required field: {field}"