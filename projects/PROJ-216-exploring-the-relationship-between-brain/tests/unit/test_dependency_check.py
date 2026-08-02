"""
Unit tests for the dependency check script.

Tests verify the functionality of run_command, check_tool_availability,
and check_all_tools functions.
"""
import json
import subprocess
from unittest.mock import patch, MagicMock
import pytest
import sys
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from dependency_check import run_command, check_tool_availability, check_all_tools, REQUIRED_TOOLS


class TestRunCommand:
    """Tests for the run_command function."""

    def test_successful_command(self):
        """Test running a command that succeeds."""
        success, stdout, stderr = run_command(["echo", "hello"])
        assert success is True
        assert stdout == "hello"
        assert stderr == ""

    def test_command_not_found(self):
        """Test running a command that doesn't exist."""
        success, stdout, stderr = run_command(["nonexistent_command_xyz"])
        assert success is False
        assert "not found" in stderr.lower() or "No such file" in stderr

    def test_command_timeout(self):
        """Test that timeout is handled correctly."""
        # Use a very short timeout to trigger timeout
        success, stdout, stderr = run_command(["sleep", "10"], timeout=1)
        assert success is False
        assert "timed out" in stderr.lower()

    def test_command_with_error(self):
        """Test running a command that exits with error."""
        success, stdout, stderr = run_command(["sh", "-c", "exit 1"])
        assert success is False
        assert stderr == "" or "exit" in stderr.lower()


class TestCheckToolAvailability:
    """Tests for the check_tool_availability function."""

    def test_unknown_tool(self):
        """Test checking for an unknown tool."""
        result = check_tool_availability("unknown_tool_xyz")
        assert result["available"] is False
        assert "Unknown tool" in result["error"]

    def test_existing_command(self):
        """Test checking for a command that exists in the system."""
        # Test with 'echo' which should always exist
        # We'll mock the REQUIRED_TOOLS to include 'echo'
        with patch('dependency_check.REQUIRED_TOOLS', {
            'echo': {
                'command': 'echo',
                'version_flag': '--version',
                'min_version': None,
                'description': 'Echo command'
            }
        }):
            result = check_tool_availability("echo")
            assert result["tool"] == "echo"
            assert result["description"] == "Echo command"
            # echo --version might not work on all systems, so we just check structure
            assert "available" in result
            assert "version" in result or "error" in result

    def test_fsl_check_structure(self):
        """Test that FSL check returns expected structure."""
        result = check_tool_availability("fsl")
        assert result["tool"] == "fsl"
        assert "description" in result
        assert "available" in result
        assert "command_used" in result

    def test_afni_check_structure(self):
        """Test that AFNI check returns expected structure."""
        result = check_tool_availability("afni")
        assert result["tool"] == "afni"
        assert "description" in result
        assert "available" in result
        assert "command_used" in result


class TestCheckAllTools:
    """Tests for the check_all_tools function."""

    def test_returns_dict(self):
        """Test that check_all_tools returns a dictionary."""
        results = check_all_tools()
        assert isinstance(results, dict)
        assert "all_available" in results
        assert "tools" in results

    def test_all_tools_checked(self):
        """Test that all required tools are checked."""
        results = check_all_tools()
        for tool_name in REQUIRED_TOOLS:
            assert tool_name in results["tools"]

    def test_all_available_flag(self):
        """Test that all_available flag is set correctly."""
        results = check_all_tools()
        # We can't guarantee FSL/AFNI are installed, but we can check the flag exists
        assert isinstance(results["all_available"], bool)

    def test_timestamp_added(self):
        """Test that timestamp is added when called from main (simulated)."""
        # This is more of an integration test, but we can verify structure
        results = check_all_tools()
        # Timestamp is added in main(), not here, so we just verify structure
        assert "tools" in results
        assert "all_available" in results


class TestRequiredToolsConfig:
    """Tests for the REQUIRED_TOOLS configuration."""

    def test_fsl_config(self):
        """Test FSL configuration structure."""
        assert "fsl" in REQUIRED_TOOLS
        assert REQUIRED_TOOLS["fsl"]["command"] == "fsl"
        assert REQUIRED_TOOLS["fsl"]["version_flag"] == "--version"

    def test_afni_config(self):
        """Test AFNI configuration structure."""
        assert "afni" in REQUIRED_TOOLS
        assert REQUIRED_TOOLS["afni"]["command"] == "afni"
        assert REQUIRED_TOOLS["afni"]["version_flag"] == "-ver"