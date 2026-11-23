"""
Unit tests for T042: Cleanup and Linting utilities.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
# Note: We import from the source location relative to the test file
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.cleanup_and_lint import (
    run_command,
    get_project_root,
    run_ruff_check,
    run_ruff_format,
    run_ruff_fix,
)


class TestRunCommand:
    def test_run_command_success(self):
        """Test running a command that succeeds."""
        result = run_command(["echo", "hello"])
        assert result["success"] is True
        assert result["return_code"] == 0
        assert "hello" in result["stdout"]

    def test_run_command_failure(self):
        """Test running a command that fails."""
        result = run_command(["sh", "-c", "exit 1"])
        assert result["success"] is False
        assert result["return_code"] == 1

    def test_run_command_not_found(self):
        """Test running a command that does not exist."""
        result = run_command(["nonexistent_command_xyz"])
        assert result["success"] is False
        assert result["return_code"] == -1
        assert "not found" in result["stderr"].lower()


class TestGetProjectRoot:
    def test_get_project_root(self):
        """Test that get_project_root returns a valid Path."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()


class TestRuffIntegration:
    """Integration tests for Ruff commands. These may be skipped if ruff is not installed."""

    @pytest.mark.skipif(
        not os.system("ruff --version > /dev/null 2>&1") == 0,
        reason="ruff is not installed"
    )
    def test_run_ruff_check(self, tmp_path):
        """Test ruff check on a temporary directory."""
        # Create a dummy file
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\n")

        with patch("src.utils.cleanup_and_lint.get_project_root", return_value=tmp_path):
            result = run_ruff_check(tmp_path)
            # Should succeed (no errors in simple import) or fail with 0 issues found
            # Ruff returns 0 if no issues, 1 if issues found
            assert "stdout" in result
            assert "stderr" in result

    @pytest.mark.skipif(
        not os.system("ruff --version > /dev/null 2>&1") == 0,
        reason="ruff is not installed"
    )
    def test_run_ruff_fix(self, tmp_path):
        """Test ruff fix on a temporary directory."""
        # Create a file with an unused import
        test_file = tmp_path / "test.py"
        test_file.write_text("import os\nimport sys\nprint('hello')\n")

        with patch("src.utils.cleanup_and_lint.get_project_root", return_value=tmp_path):
            result = run_ruff_fix(tmp_path)
            # Should attempt to fix
            assert "command" in result

    @pytest.mark.skipif(
        not os.system("black --version > /dev/null 2>&1") == 0,
        reason="black is not installed"
    )
    def test_run_ruff_format_fallback_to_black(self, tmp_path):
        """Test that formatting falls back to black if ruff format is missing."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x=1+2\n")

        with patch("src.utils.cleanup_and_lint.get_project_root", return_value=tmp_path):
            # Mock ruff format to fail with "not found"
            with patch("src.utils.cleanup_and_lint.run_command") as mock_run:
                mock_run.side_effect = [
                    {"success": False, "stderr": "No such file or directory", "stdout": ""},
                    {"success": True, "stdout": "reformatted 1 file", "stderr": "", "return_code": 0}
                ]
                result = run_ruff_format(tmp_path)
                # Should have called run_command twice
                assert mock_run.call_count == 2
                # Second call should be black
                assert "black" in mock_run.call_args_list[1][0][0][0]