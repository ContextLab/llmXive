"""
Unit tests for the dependency check module.
"""

import subprocess
from unittest.mock import patch, MagicMock
import pytest

from code.dependency_check import run_command, check_tool_availability, check_all_tools


class TestRunCommand:
    def test_successful_command(self):
        """Test run_command with a successful execution."""
        with patch('code.dependency_check.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="success output",
                stderr=""
            )
            success, output = run_command(["echo", "test"])
            assert success is True
            assert output == "success output"

    def test_failed_command(self):
        """Test run_command with a failed execution."""
        with patch('code.dependency_check.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="error message"
            )
            success, output = run_command(["false"])
            assert success is False
            assert output == "error message"

    def test_timeout(self):
        """Test run_command with a timeout."""
        with patch('code.dependency_check.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["test"], timeout=30)
            success, output = run_command(["slow_command"])
            assert success is False
            assert "timed out" in output

    def test_file_not_found(self):
        """Test run_command when command is not found."""
        with patch('code.dependency_check.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            success, output = run_command(["nonexistent_command"])
            assert success is False
            assert "not found" in output


class TestCheckToolAvailability:
    def test_tool_available(self):
        """Test check_tool_availability when tool is available."""
        with patch('code.dependency_check.run_command') as mock_run:
            mock_run.return_value = (True, "1.0.0")
            result = check_tool_availability("fsl", ["fslversion"])
            assert result["available"] is True
            assert result["version"] == "1.0.0"
            assert result["error"] is None

    def test_tool_unavailable(self):
        """Test check_tool_availability when tool is unavailable."""
        with patch('code.dependency_check.run_command') as mock_run:
            mock_run.return_value = (False, "command not found")
            result = check_tool_availability("fsl", ["fslversion"])
            assert result["available"] is False
            assert result["version"] is None
            assert result["error"] == "command not found"


class TestCheckAllTools:
    def test_all_tools_available(self):
        """Test check_all_tools when both FSL and AFNI are available."""
        with patch('code.dependency_check.check_tool_availability') as mock_check:
            mock_check.side_effect = [
                {"available": True, "version": "6.0.0", "error": None},  # FSL
                {"available": True, "version": "20.0", "error": None}    # AFNI
            ]
            results = check_all_tools()
            assert results["summary"]["all_available"] is True
            assert "missing_tools" not in results["summary"]

    def test_fsl_missing(self):
        """Test check_all_tools when FSL is missing."""
        with patch('code.dependency_check.check_tool_availability') as mock_check:
            mock_check.side_effect = [
                {"available": False, "version": None, "error": "not found"},  # FSL
                {"available": True, "version": "20.0", "error": None}         # AFNI
            ]
            results = check_all_tools()
            assert results["summary"]["all_available"] is False
            assert "FSL" in results["summary"]["missing_tools"]

    def test_afni_missing(self):
        """Test check_all_tools when AFNI is missing."""
        with patch('code.dependency_check.check_tool_availability') as mock_check:
            mock_check.side_effect = [
                {"available": True, "version": "6.0.0", "error": None},  # FSL
                {"available": False, "version": None, "error": "not found"} # AFNI
            ]
            results = check_all_tools()
            assert results["summary"]["all_available"] is False
            assert "AFNI" in results["summary"]["missing_tools"]

    def test_both_missing(self):
        """Test check_all_tools when both FSL and AFNI are missing."""
        with patch('code.dependency_check.check_tool_availability') as mock_check:
            mock_check.side_effect = [
                {"available": False, "version": None, "error": "not found"},  # FSL
                {"available": False, "version": None, "error": "not found"}   # AFNI
            ]
            results = check_all_tools()
            assert results["summary"]["all_available"] is False
            assert "FSL" in results["summary"]["missing_tools"]
            assert "AFNI" in results["summary"]["missing_tools"]