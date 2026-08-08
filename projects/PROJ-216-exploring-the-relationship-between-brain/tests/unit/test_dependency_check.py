import os
import sys
import json
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from dependency_check import run_command, check_tool_availability, check_all_tools

class TestRunCommand:
    def test_successful_command(self):
        """Test run_command with a successful command."""
        success, output = run_command(["echo", "hello"])
        assert success is True
        assert output == "hello"

    def test_failed_command(self):
        """Test run_command with a failing command."""
        success, output = run_command(["false"])
        assert success is False

    def test_command_not_found(self):
        """Test run_command with a non-existent command."""
        success, output = run_command(["nonexistent_command_xyz"])
        assert success is False
        assert "not found" in output.lower() or "No such file" in output

    def test_timeout(self):
        """Test run_command with a timeout."""
        # Use sleep to create a timeout scenario
        success, output = run_command(["sleep", "10"], timeout=1)
        assert success is False
        assert "timed out" in output.lower()

class TestCheckToolAvailability:
    @patch('dependency_check.run_command')
    def test_available_tool(self, mock_run):
        """Test check_tool_availability with an available tool."""
        mock_run.return_value = (True, "1.0.0")
        result = check_tool_availability("test_tool", ["--version"])
        
        assert result["tool"] == "test_tool"
        assert result["available"] is True
        assert result["version_output"] == "1.0.0"
        assert result["error"] is None

    @patch('dependency_check.run_command')
    def test_unavailable_tool(self, mock_run):
        """Test check_tool_availability with an unavailable tool."""
        mock_run.return_value = (False, "command not found")
        result = check_tool_availability("missing_tool", ["--version"])
        
        assert result["tool"] == "missing_tool"
        assert result["available"] is False
        assert result["version_output"] is None
        assert result["error"] == "command not found"

class TestCheckAllTools:
    @patch('dependency_check.check_tool_availability')
    def test_all_tools_available(self, mock_check):
        """Test check_all_tools when all tools are available."""
        # Mock FSL check
        mock_check.side_effect = [
            {"tool": "fsl", "available": True, "version_output": "6.0.0", "error": None},
            {"tool": "afni", "available": True, "version_output": "20.0.0", "error": None}
        ]
        
        # We need to patch specifically for FSL and AFNI calls
        def side_effect(tool, args):
            if tool == "fsl":
                return {"tool": "fsl", "available": True, "version_output": "6.0.0", "error": None}
            elif tool == "afni":
                return {"tool": "afni", "available": True, "version_output": "20.0.0", "error": None}
            return {"tool": tool, "available": False, "version_output": None, "error": "not found"}
        
        mock_check.side_effect = side_effect
        
        result = check_all_tools()
        
        assert result["all_available"] is True
        assert "FSL" in result["tools"]
        assert "AFNI" in result["tools"]
        assert len(result["missing_tools"]) == 0

    @patch('dependency_check.check_tool_availability')
    def test_some_tools_missing(self, mock_check):
        """Test check_all_tools when some tools are missing."""
        def side_effect(tool, args):
            if tool == "fsl":
                return {"tool": "fsl", "available": True, "version_output": "6.0.0", "error": None}
            elif tool == "afni":
                return {"tool": "afni", "available": False, "version_output": None, "error": "not found"}
            return {"tool": tool, "available": False, "version_output": None, "error": "not found"}
        
        mock_check.side_effect = side_effect
        
        result = check_all_tools()
        
        assert result["all_available"] is False
        assert "AFNI" in result["missing_tools"]

class TestDependencyCheckIntegration:
    def test_dependency_check_output_file(self):
        """Test that dependency_check.py creates the expected output file."""
        # Run the main function
        from dependency_check import main
        
        # Capture exit code
        try:
            main()
        except SystemExit as e:
            # Expected exit
            pass
        
        # Check if file was created
        output_file = Path("data/processed/dependency_check.json")
        assert output_file.exists(), "dependency_check.json should be created"
        
        # Verify JSON structure
        with open(output_file) as f:
            data = json.load(f)
        
        assert "tools" in data
        assert "all_available" in data
        assert "missing_tools" in data
        assert "FSL" in data["tools"]
        assert "AFNI" in data["tools"]