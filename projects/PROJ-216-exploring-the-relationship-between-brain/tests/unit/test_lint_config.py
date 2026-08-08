"""
Unit tests to verify linting and formatting configuration.
These tests ensure that ruff and black are properly configured
and that the project adheres to the defined style guidelines.
"""
import subprocess
import sys
from pathlib import Path

import pytest


class TestLintConfig:
    """Tests for linting and formatting tool configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_ruff_config_exists(self, project_root):
        """Verify that ruff configuration exists in pyproject.toml."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"

        content = pyproject.read_text()
        assert "[tool.ruff]" in content, "ruff configuration must be present in pyproject.toml"

    def test_black_config_exists(self, project_root):
        """Verify that black configuration exists in pyproject.toml."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"

        content = pyproject.read_text()
        assert "[tool.black]" in content, "black configuration must be present in pyproject.toml"

    def test_ruff_check_passes(self, project_root):
        """Run ruff check and ensure it passes (exit code 0)."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", "code", "tests"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            # ruff returns 0 if no issues, 1 if issues found
            # We expect this to pass if the codebase is clean
            # If ruff is not installed, skip the test
            if result.returncode == 127 or "No module named 'ruff'" in result.stderr:
                pytest.skip("ruff not installed")
            # If there are linting errors, the test fails
            assert result.returncode == 0, f"ruff check failed:\n{result.stdout}\n{result.stderr}"
        except FileNotFoundError:
            pytest.skip("ruff executable not found")

    def test_black_check_passes(self, project_root):
        """Run black check and ensure it passes (exit code 0)."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "code", "tests"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            # black returns 0 if files are already formatted, 1 if they would be changed
            if result.returncode == 127 or "No module named 'black'" in result.stderr:
                pytest.skip("black not installed")
            assert result.returncode == 0, f"black check failed:\n{result.stdout}\n{result.stderr}"
        except FileNotFoundError:
            pytest.skip("black executable not found")

    def test_isort_config_exists(self, project_root):
        """Verify that isort configuration is present in ruff settings."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"

        content = pyproject.read_text()
        assert "[tool.ruff.isort]" in content, "isort configuration must be present in pyproject.toml"

    def test_line_length_consistency(self, project_root):
        """Verify that black and ruff use the same line length."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()

        # Extract line-length from black config
        black_line_length = None
        ruff_line_length = None

        in_black = False
        in_ruff = False
        for line in content.split("\n"):
            if "[tool.black]" in line:
                in_black = True
                in_ruff = False
            elif "[tool.ruff]" in line:
                in_ruff = True
                in_black = False
            elif in_black and "line-length" in line:
                black_line_length = int(line.split("=")[1].strip())
            elif in_ruff and "line-length" in line:
                ruff_line_length = int(line.split("=")[1].strip())

        assert black_line_length is not None, "black line-length not configured"
        assert ruff_line_length is not None, "ruff line-length not configured"
        assert black_line_length == ruff_line_length, (
            f"Line length mismatch: black={black_line_length}, ruff={ruff_line_length}"
        )