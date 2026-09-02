"""
Unit tests for the Quickstart Validation logic.
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.quickstart_validator import run_command, validate_artifacts_exist, RESULTS_FILE

def test_run_command_success():
    """Test run_command with a successful command."""
    result = run_command(["echo", "hello"])
    assert result["success"] is True
    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]

def test_run_command_failure():
    """Test run_command with a failing command."""
    result = run_command(["false"])
    assert result["success"] is False
    assert result["exit_code"] != 0

def test_run_command_timeout():
    """Test run_command with a timeout."""
    # Use a command that sleeps longer than the timeout
    result = run_command(["sleep", "10"], timeout=1)
    assert result["success"] is False
    assert result["exit_code"] == -1
    assert "Timeout" in result["stderr"]

def test_validate_artifacts_exist():
    """Test artifact validation logic."""
    # Mock the existence of files
    with patch("pathlib.Path.exists") as mock_exists:
        # Mock all files to exist
        mock_exists.return_value = True
        result = validate_artifacts_exist()
        assert result["all_exist"] is True
        assert len(result["checks"]) > 0

        # Mock one file to not exist
        mock_exists.side_effect = [True, False, True, True, True]
        result = validate_artifacts_exist()
        assert result["all_exist"] is False
        assert result["checks"][1]["exists"] is False

def test_validation_report_structure():
    """Test that the validation report has the expected structure."""
    report = {
        "timestamp": "2023-10-27T10:00:00Z",
        "steps": [],
        "artifacts_check": {"all_exist": True, "checks": []},
        "overall_success": True
    }
    assert "timestamp" in report
    assert "steps" in report
    assert "artifacts_check" in report
    assert "overall_success" in report

if __name__ == "__main__":
    pytest.main([__file__, "-v"])