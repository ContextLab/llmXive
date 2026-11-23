"""
Contract tests for linting and formatting configuration.

These tests verify that the project's linting (ruff) and formatting (black)
configurations are correctly set up and can be executed.
"""
import subprocess
import sys
from pathlib import Path
import pytest


class TestLintingConfiguration:
    """Tests for ruff linting setup."""

    def test_ruff_is_installed(self):
        """Verify that ruff is available in the environment."""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "ruff"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Ruff must be installed"

    def test_ruff_config_exists(self):
        """Verify that ruff configuration file exists."""
        project_root = Path(__file__).parent.parent.parent
        pyproject = project_root / "code" / "pyproject.toml"
        ruff_config = project_root / "code" / ".ruff.toml"
        
        # At least one config file should exist
        assert pyproject.exists() or ruff_config.exists(), \
            "Ruff configuration must exist in code/pyproject.toml or code/.ruff.toml"

    def test_ruff_check_runs(self):
        """Verify that ruff can successfully run a check on the code directory."""
        project_root = Path(__file__).parent.parent.parent
        code_dir = project_root / "code"
        
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Ruff should run without crashing (return code 0 or 1 is acceptable)
        # Return code 0 means no issues, 1 means issues found but check passed
        assert result.returncode in (0, 1), \
            f"Ruff check failed with unexpected error: {result.stderr}"


class TestFormattingConfiguration:
    """Tests for black formatting setup."""

    def test_black_is_installed(self):
        """Verify that black is available in the environment."""
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "black"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Black must be installed"

    def test_black_config_exists(self):
        """Verify that black configuration is present."""
        project_root = Path(__file__).parent.parent.parent
        pyproject = project_root / "code" / "pyproject.toml"
        
        assert pyproject.exists(), \
            "Black configuration must exist in code/pyproject.toml"
        
        # Check that [tool.black] section exists
        content = pyproject.read_text()
        assert "[tool.black]" in content, \
            "Black configuration section [tool.black] must be present"

    def test_black_check_runs(self):
        """Verify that black can successfully run a check on the code directory."""
        project_root = Path(__file__).parent.parent.parent
        code_dir = project_root / "code"
        
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(code_dir)],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        # Black should run without crashing (return code 0 or 1 is acceptable)
        # Return code 0 means all files formatted, 1 means some files need formatting
        assert result.returncode in (0, 1), \
            f"Black check failed with unexpected error: {result.stderr}"


class TestLintFormatScript:
    """Tests for the lint_format_config.py utility script."""

    def test_script_imports_successfully(self):
        """Verify that the lint_format_config module can be imported."""
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root / "code"))
        
        try:
            from lint_format_config import run_command, check_code, fix_code
            assert callable(run_command)
            assert callable(check_code)
            assert callable(fix_code)
        finally:
            sys.path.pop(0)

    def test_run_command_functionality(self):
        """Verify that run_command can execute a simple command."""
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root / "code"))
        
        try:
            from lint_format_config import run_command
            
            success, output = run_command(
                [sys.executable, "--version"],
                "Python version check"
            )
            
            assert success is True, "run_command should succeed for valid command"
            assert "Python" in output, "Output should contain Python version"
        finally:
            sys.path.pop(0)
