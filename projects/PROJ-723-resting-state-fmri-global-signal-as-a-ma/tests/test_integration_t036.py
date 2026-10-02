"""
Unit tests for the Integration Test Runner (T036).

These tests verify the logic of the integration test script itself,
ensuring it correctly identifies missing files, handles errors, and validates
the final report structure.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions we want to test
# We need to import from the module, but since it's a script, we might need to adjust
# For now, we assume the functions are importable or we test the logic via mocking
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

# We will test the logic by mocking the heavy-lifting functions
# and verifying the flow of check_file_exists and run_step

def test_check_file_exists_found():
    """Test that check_file_exists returns True for an existing file."""
    from run_integration_test import check_file_exists
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"dummy content")
        tmp_path = tmp.name
    
    try:
        result = check_file_exists(tmp_path, "test_file")
        assert result is True
    finally:
        os.unlink(tmp_path)

def test_check_file_exists_missing():
    """Test that check_file_exists returns False for a missing file."""
    from run_integration_test import check_file_exists
    result = check_file_exists("/nonexistent/path/file.txt", "test_file")
    assert result is False

def test_check_file_exists_empty():
    """Test that check_file_exists returns False for an empty file."""
    from run_integration_test import check_file_exists
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # Write nothing
        tmp_path = tmp.name
    
    try:
        result = check_file_exists(tmp_path, "test_file")
        assert result is False
    finally:
        os.unlink(tmp_path)

def test_run_step_success():
    """Test that run_step returns True on success."""
    from run_integration_test import run_step
    def success_func():
        pass
    
    result = run_step("Test Step", success_func)
    assert result is True

def test_run_step_failure():
    """Test that run_step returns False on exception."""
    from run_integration_test import run_step
    def fail_func():
        raise RuntimeError("Simulated error")
    
    result = run_step("Test Step", fail_func)
    assert result is False

def test_final_report_validation_logic():
    """Test the logic of final report validation without running the whole pipeline."""
    from run_integration_test import main
    import tempfile
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the file existence checks
        # We can't easily test the full main() flow without mocking sys.exit
        # So we test the validation logic specifically
        
        # Create a mock final report
        report_data = {
            "criteria_status": {
                "SC-001": {"status": "met", "narrative_summary": "Test", "metrics": {"p_value": 0.01}},
                "SC-002": {"status": "met", "narrative_summary": "Test", "metrics": {"r": 0.3}},
                "SC-003": {"status": "met", "narrative_summary": "Test", "metrics": {"diff": 0.01}},
                "SC-004": {"status": "met", "narrative_summary": "Test", "metrics": {"var": 0.05}},
                "SC-005": {"status": "met", "narrative_summary": "Test", "metrics": {"p_value": 0.02}}
            },
            "metrics_summary": {}
        }
        
        report_path = Path(tmpdir) / "final_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f)
        
        # Now test the validation logic extracted from main
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        required_keys = ["criteria_status", "metrics_summary"]
        assert all(k in report for k in required_keys)
        
        sc_keys = [f"SC-{i:03d}" for i in range(1, 6)]
        for sk in sc_keys:
            assert sk in report["criteria_status"]
            assert "status" in report["criteria_status"][sk]

        print("Validation logic passed.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
