"""
Contract test to verify linting and formatting configuration is correctly set up.

This test ensures that:
1. ruff and black are installed and accessible
2. Configuration files (pyproject.toml, .ruff.toml, .black.toml) exist
3. The lint_format_config module can be imported and executed
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestLintingConfiguration:
    """Tests for linting and formatting tool configuration."""

    @pytest.fixture
    def project_root(self):
        """Return the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_ruff_is_installed(self, project_root):
        """Verify ruff is installed and accessible."""
        result = subprocess.run(
            ["ruff", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Ruff not installed: {result.stderr}"
        assert "ruff" in result.stdout.lower()

    def test_black_is_installed(self, project_root):
        """Verify black is installed and accessible."""
        result = subprocess.run(
            ["black", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Black not installed: {result.stderr}"
        assert "black" in result.stdout.lower()

    def test_pyproject_toml_exists(self, project_root):
        """Verify pyproject.toml exists with configuration."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"

        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
        assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"

    def test_ruff_config_file_exists(self, project_root):
        """Verify .ruff.toml or ruff section exists."""
        ruff_toml = project_root / ".ruff.toml"
        pyproject_path = project_root / "pyproject.toml"

        # Either a separate file or section in pyproject.toml should exist
        assert (
            ruff_toml.exists() or
            "[tool.ruff]" in pyproject_path.read_text()
        ), "Ruff configuration not found"

    def test_black_config_file_exists(self, project_root):
        """Verify .black.toml or black section exists."""
        black_toml = project_root / ".black.toml"
        pyproject_path = project_root / "pyproject.toml"

        # Either a separate file or section in pyproject.toml should exist
        assert (
            black_toml.exists() or
            "[tool.black]" in pyproject_path.read_text()
        ), "Black configuration not found"

    def test_lint_format_config_module_importable(self, project_root):
        """Verify the lint_format_config module can be imported."""
        sys.path.insert(0, str(project_root / "code"))
        try:
            from lint_format_config import run_command, check_code, fix_code
            assert callable(run_command)
            assert callable(check_code)
            assert callable(fix_code)
        finally:
            sys.path.pop(0)

    def test_check_code_function_exists(self, project_root):
        """Verify check_code function runs without import errors."""
        sys.path.insert(0, str(project_root / "code"))
        try:
            from lint_format_config import check_code
            exit_code, message = check_code()
            # We expect this to return an exit code (0 or 1) and a message
            assert isinstance(exit_code, int)
            assert isinstance(message, str)
        finally:
            sys.path.pop(0)
