"""
Unit tests for verify_env.py

Tests the logic for checking tool availability in the system PATH.
"""
import subprocess
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module to test
# We need to import from the code directory relative to tests
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
import verify_env


class TestVerifyEnv(unittest.TestCase):
    """Test cases for verify_env module."""

    @patch("verify_env.subprocess.run")
    def test_tool_found_unix(self, mock_run):
        """Test that a found tool returns True on Unix."""
        mock_run.return_value = MagicMock(returncode=0)
        self.assertTrue(verify_env.check_tool_availability("fsl"))
        mock_run.assert_called_once_with(
            ["which", "fsl"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    @patch("verify_env.subprocess.run")
    def test_tool_not_found_unix(self, mock_run):
        """Test that a missing tool returns False on Unix."""
        mock_run.return_value = MagicMock(returncode=1)
        self.assertFalse(verify_env.check_tool_availability("fsl"))

    @patch("verify_env.subprocess.run")
    def test_tool_found_windows(self, mock_run):
        """Test that a found tool returns True on Windows."""
        # Mock sys.platform to simulate Windows
        with patch.object(verify_env.sys, 'platform', 'win32'):
            mock_run.return_value = MagicMock(returncode=0)
            self.assertTrue(verify_env.check_tool_availability("afni"))
            mock_run.assert_called_once_with(
                ["where", "afni"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

    @patch("verify_env.subprocess.run")
    def test_tool_not_found_windows(self, mock_run):
        """Test that a missing tool returns False on Windows."""
        with patch.object(verify_env.sys, 'platform', 'win32'):
            mock_run.return_value = MagicMock(returncode=1)
            self.assertFalse(verify_env.check_tool_availability("afni"))

    @patch("verify_env.sys.exit")
    @patch("verify_env.check_tool_availability")
    def test_main_all_present(self, mock_check, mock_exit):
        """Test main() exits with 0 when all tools are present."""
        # Mock all tools as present
        mock_check.side_effect = lambda x: True

        verify_env.main()

        mock_exit.assert_called_once_with(0)
        # Ensure all required tools were checked
        self.assertEqual(mock_check.call_count, len(verify_env.REQUIRED_TOOLS))

    @patch("verify_env.sys.exit")
    @patch("verify_env.check_tool_availability")
    def test_main_missing_tool(self, mock_check, mock_exit):
        """Test main() exits with 1 when a tool is missing."""
        # Mock 'fsl' as missing, others present
        def mock_side_effect(tool):
            return tool != "fsl"

        mock_check.side_effect = mock_side_effect

        with patch("builtins.print") as mock_print:
            verify_env.main()

            mock_exit.assert_called_once_with(1)
            # Verify error message contains the missing tool name
            mock_print.assert_called()
            error_output = str(mock_print.call_args)
            self.assertIn("fsl", error_output)
            self.assertIn("Required tools not found", error_output)


if __name__ == "__main__":
    unittest.main()