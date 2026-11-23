"""
Unit tests for the linting runner script.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from linting_runner import run_ruff_check, run_ruff_fix, generate_report

class TestLintingFunctions:
    
    def test_run_ruff_check_success(self):
        """Test successful ruff check execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            success, output = run_ruff_check(Path("/fake/root"))
            assert success is True
            assert output == ""
            mock_run.assert_called_once()

    def test_run_ruff_check_failure(self):
        """Test failed ruff check execution (lint errors found)."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="E501 line too long\n", stderr="")
            success, output = run_ruff_check(Path("/fake/root"))
            assert success is False
            assert "E501" in output

    def test_run_ruff_check_timeout(self):
        """Test ruff check timeout."""
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired(cmd="ruff", timeout=120)
            success, output = run_ruff_check(Path("/fake/root"))
            assert success is False
            assert "timed out" in output.lower()

    def test_run_ruff_fix_success(self):
        """Test successful ruff fix execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Fixed 1 issue\n", stderr="")
            success, output = run_ruff_fix(Path("/fake/root"))
            assert success is True
            assert "Fixed" in output

    def test_generate_report_success(self):
        """Test report generation when linting passes."""
        report = generate_report(True, "")
        assert "PASSED" in report
        assert "All linting checks passed successfully" in report

    def test_generate_report_failure_with_fix(self):
        """Test report generation when linting fails but fix succeeds."""
        report = generate_report(False, "Error\n", True, "Fixed\n")
        assert "FAILED" in report
        assert "Auto-Fix Attempt" in report
        assert "PASSED" in report.split("Auto-Fix Attempt")[1].split("\n")[1]

    def test_generate_report_failure_no_fix(self):
        """Test report generation when linting fails and fix fails."""
        report = generate_report(False, "Error\n", False, "Fix Failed\n")
        assert "FAILED" in report
        assert "FAILED (or not attempted)" in report