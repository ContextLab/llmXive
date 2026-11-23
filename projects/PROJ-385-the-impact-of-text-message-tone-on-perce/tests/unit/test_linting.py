"""
Unit tests for T034: Linting and formatting checks.

These tests verify that the linting script exists, is executable,
and that the codebase passes the configured linting rules.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from config import get_code_dir, get_project_root


class TestLintingTask:
    """Tests for the linting task T034."""

    @pytest.fixture
    def code_dir(self):
        """Get the code directory path."""
        return get_code_dir()

    @pytest.fixture
    def linting_script(self):
        """Get the path to the linting script."""
        return get_project_root() / "code" / "06_run_linting.py"

    def test_linting_script_exists(self, linting_script):
        """Verify that the linting script exists."""
        assert linting_script.exists(), f"Linting script not found at {linting_script}"

    def test_linting_script_is_executable(self, linting_script):
        """Verify that the linting script can be imported."""
        # Try importing the module to ensure it's syntactically valid
        spec = importlib.util.spec_from_file_location("run_linting", linting_script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "main"), "Linting script must have a main() function"

    def test_ruff_check_passes(self, code_dir):
        """Verify that ruff check passes with 0 errors."""
        project_root = get_project_root()
        result = subprocess.run(
            ["python", "-m", "ruff", "check", str(code_dir)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_black_check_passes(self, code_dir):
        """Verify that black --check passes with 0 errors."""
        project_root = get_project_root()
        result = subprocess.run(
            ["python", "-m", "black", "--check", str(code_dir)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Black check failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_linting_script_run_succeeds(self, linting_script):
        """Verify that running the linting script succeeds."""
        result = subprocess.run(
            ["python", str(linting_script)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, (
            f"Linting script failed:\n{result.stdout}\n{result.stderr}"
        )


# Import here to avoid circular imports at module level
import importlib.util
