"""
Unit tests for the linting and formatting configuration module.

Note: These tests verify that the module imports correctly and that
the command execution logic is sound. They do not actually run ruff/black
on the full codebase to avoid side effects during testing, but they
test the helper function `run_command`.
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
# Assuming the test is run from the project root or code is in path
try:
    from code.lint_format import run_command, main
except ImportError:
    # Fallback for if the test is run directly from the tests directory
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from lint_format import run_command, main
from pathlib import Path


def test_run_command_success():
    """Test run_command with a successful execution."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = run_command(["echo", "hello"], check=True)

        mock_run.assert_called_once()
        assert result.returncode == 0
        assert result.stdout == "output"


def test_run_command_failure_with_check():
    """Test run_command raises exception when check=True and exit code != 0."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ["cmd"])

        with pytest.raises(subprocess.CalledProcessError):
            run_command(["failing_cmd"], check=True)


def test_run_command_failure_without_check():
    """Test run_command returns result when check=False and exit code != 0."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_run.return_value = mock_result

        result = run_command(["failing_cmd"], check=False)

        assert result.returncode == 1
        assert result.stderr == "error"
        mock_run.assert_called_once()


def test_main_missing_tools_install_success():
    """Test main() when tools are missing but install succeeds."""
    with patch("subprocess.run") as mock_run:
        # First call (check ruff) fails
        # Second call (check black) fails
        # Third call (install) succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "ruff"), # check ruff
            subprocess.CalledProcessError(1, "black"), # check black
            MagicMock(returncode=0), # install
            MagicMock(returncode=0), # ruff check (success)
            MagicMock(returncode=0), # black check (success)
        ]

        # Mock Path.exists to return True
        with patch("code.lint_format.Path.exists", return_value=True):
            # Mock print to avoid output noise
            with patch("builtins.print"):
                exit_code = main()
        
        # Verify install was called
        install_call = mock_run.call_args_list[2]
        assert "pip" in install_call[0][0]
        assert "ruff" in install_call[0][0]
        assert "black" in install_call[0][0]
        
        # Verify main returns 0 on success
        assert exit_code == 0


def test_main_lint_failure():
    """Test main() returns 1 if linting fails."""
    with patch("subprocess.run") as mock_run:
        # Tools exist
        mock_run.return_value = MagicMock(returncode=0) # check version
        
        # But ruff check fails
        mock_ruff_fail = MagicMock(returncode=1, stdout="Error", stderr="")
        mock_black_ok = MagicMock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = [
            MagicMock(returncode=0), # ruff version
            MagicMock(returncode=0), # black version
            mock_ruff_fail,          # ruff check
        ]

        with patch("code.lint_format.Path.exists", return_value=True):
            with patch("builtins.print"):
                exit_code = main()
        
        assert exit_code == 1


def test_main_format_failure():
    """Test main() returns 1 if formatting check fails."""
    with patch("subprocess.run") as mock_run:
        # Tools exist
        mock_run.return_value = MagicMock(returncode=0) # check version
        
        # Ruff ok, Black fails
        mock_ruff_ok = MagicMock(returncode=0, stdout="", stderr="")
        mock_black_fail = MagicMock(returncode=1, stdout="Diff", stderr="")
        
        mock_run.side_effect = [
            MagicMock(returncode=0), # ruff version
            MagicMock(returncode=0), # black version
            mock_ruff_ok,            # ruff check
            mock_black_fail,         # black check
        ]

        with patch("code.lint_format.Path.exists", return_value=True):
            with patch("builtins.print"):
                exit_code = main()
        
        assert exit_code == 1