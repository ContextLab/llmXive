"""
Tests for linting and formatting configuration.
Validates that ruff and black are properly configured and can be invoked.
"""
import os
import subprocess
import sys
import tempfile
import shutil
import pytest
from pathlib import Path


class TestLintingConfig:
    """Test suite for linting configuration validation."""

    def test_ruff_config_exists(self):
        """Verify that ruff configuration is present in pyproject.toml."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml must exist"

        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration section missing from pyproject.toml"

    def test_black_config_exists(self):
        """Verify that black configuration is present in pyproject.toml."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml must exist"

        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "Black configuration section missing from pyproject.toml"

    def test_ruff_check_passes_on_valid_code(self):
        """Verify that ruff can check a valid Python file without errors."""
        # Create a temporary valid Python file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "valid_test.py"
            test_file.write_text("def hello():\n    return 'world'\n")

            # Run ruff check
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", str(test_file)],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )

            # Should pass (exit code 0)
            assert result.returncode == 0, f"Ruff check failed: {result.stdout} {result.stderr}"

    def test_black_format_passes_on_valid_code(self):
        """Verify that black can format a valid Python file without errors."""
        # Create a temporary valid Python file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "valid_test.py"
            test_file.write_text("def hello( ): return 'world'\n")

            # Run black check (diff mode)
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", str(test_file)],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )

            # Note: black might need to format the file, so we just check it runs without crashing
            # A properly formatted file would return 0, but we're testing configuration
            assert result.returncode in [0, 1], f"Black check crashed: {result.stderr}"

    def test_ruff_includes_required_checks(self):
        """Verify ruff configuration includes essential check codes."""
        pyproject_path = Path("pyproject.toml")
        content = pyproject_path.read_text()

        # Check for essential rule sets
        assert '"E"' in content or "'E'" in content, "Ruff should include pycodestyle errors"
        assert '"F"' in content or "'F'" in content, "Ruff should include pyflakes"

    def test_black_line_length_configured(self):
        """Verify black line length is configured to 88."""
        pyproject_path = Path("pyproject.toml")
        content = pyproject_path.read_text()

        assert "line-length = 88" in content, "Black line-length should be 88"

    def test_python_version_targeted(self):
        """Verify both tools target Python 3.11."""
        pyproject_path = Path("pyproject.toml")
        content = pyproject_path.read_text()

        # Check for Python 3.11 target
        assert "py311" in content or "3.11" in content, "Tools should target Python 3.11"