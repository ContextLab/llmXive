"""
Unit tests for the Monte-Carlo Startup Validator (Task T031).
"""
import pytest
from unittest.mock import patch, MagicMock
from code.src.audit.monte_carlo_startup_validator import run_startup_validation, main
from code.src.utils.logger import AuditLogger

def test_run_startup_validation_success():
    """Test that run_startup_validation returns True when T062 passes."""
    mock_result = {
        "status": "passed",
        "tests_passed": 4,
        "total_tests": 4
    }
    
    with patch('code.src.audit.monte_carlo_startup_validator.run_monte_carlo_validation', return_value=mock_result):
        result = run_startup_validation()
        assert result is True

def test_run_startup_validation_failure():
    """Test that run_startup_validation returns False when T062 fails."""
    mock_result = {
        "status": "failed",
        "tests_passed": 0,
        "total_tests": 4
    }
    
    with patch('code.src.audit.monte_carlo_startup_validator.run_monte_carlo_validation', return_value=mock_result):
        result = run_startup_validation()
        assert result is False

def test_run_startup_validation_exception():
    """Test that run_startup_validation handles exceptions gracefully."""
    with patch('code.src.audit.monte_carlo_startup_validator.run_monte_carlo_validation', side_effect=RuntimeError("Simulated failure")):
        result = run_startup_validation()
        assert result is False

def test_run_startup_validation_empty_result():
    """Test that run_startup_validation returns False for empty result."""
    with patch('code.src.audit.monte_carlo_startup_validator.run_monte_carlo_validation', return_value=None):
        result = run_startup_validation()
        assert result is False

def test_main_success():
    """Test that main returns 0 on success."""
    mock_result = {"status": "passed", "tests_passed": 4, "total_tests": 4}
    with patch('code.src.audit.monte_carlo_startup_validator.run_monte_carlo_validation', return_value=mock_result):
        exit_code = main()
        assert exit_code == 0

def test_main_failure():
    """Test that main returns 1 on failure."""
    mock_result = {"status": "failed", "tests_passed": 0, "total_tests": 4}
    with patch('code.src.audit.monte_carlo_startup_validator.run_monte_carlo_validation', return_value=mock_result):
        exit_code = main()
        assert exit_code == 1
