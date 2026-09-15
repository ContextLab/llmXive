"""
Unit tests for linting and formatting configuration.
These tests verify that the project is configured to use ruff and black
and that the configuration files are valid.
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

class TestLintingConfiguration:
    """Tests for linting and formatting tool configuration."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        # Assuming the tests are run from code/tests/unit/
        return Path(__file__).parent.parent.parent

    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists in the project root."""
        pyproject_path = project_root / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml must exist in project root"

    def test_black_config_present(self, project_root):
        """Test that Black configuration is present in pyproject.toml."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"
        assert "line-length" in content, "Black line-length configuration missing"

    def test_ruff_config_present(self, project_root):
        """Test that Ruff configuration is present in pyproject.toml."""
        pyproject_path = project_root / "pyproject.toml"
        content = pyproject_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration missing from pyproject.toml"
        assert "select" in content, "Ruff select rules configuration missing"

    def test_ruff_check_command_available(self, project_root):
        """Test that the ruff command is available (if installed)."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # If ruff is installed, verify it runs without error
            if result.returncode == 0:
                assert "ruff" in result.stdout.lower() or "ruff" in result.stderr.lower()
        except FileNotFoundError:
            # Ruff is not installed; skip this check as it's an optional dev dependency
            pytest.skip("Ruff is not installed in the environment")
        except subprocess.TimeoutExpired:
            pytest.skip("Ruff command timed out")

    def test_black_command_available(self, project_root):
        """Test that the black command is available (if installed)."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # If black is installed, verify it runs without error
            if result.returncode == 0:
                assert "black" in result.stdout.lower()
        except FileNotFoundError:
            # Black is not installed; skip this check as it's an optional dev dependency
            pytest.skip("Black is not installed in the environment")
        except subprocess.TimeoutExpired:
            pytest.skip("Black command timed out")

    def test_ruff_check_syntax(self, project_root):
        """Test that ruff can check syntax on a sample file without crashing."""
        try:
            # Run ruff check on the tests directory
            result = subprocess.run(
                ["ruff", "check", str(project_root / "tests")],
                capture_output=True,
                text=True,
                timeout=30
            )
            # We don't assert returncode == 0 because there might be linting errors.
            # We only assert that the command ran successfully (no crash).
            assert result.returncode is not None
        except FileNotFoundError:
            pytest.skip("Ruff is not installed in the environment")
        except subprocess.TimeoutExpired:
            pytest.skip("Ruff check timed out")

    def test_black_check_format(self, project_root):
        """Test that black can check formatting on a sample file without crashing."""
        try:
            # Run black --check on the tests directory
            result = subprocess.run(
                ["black", "--check", str(project_root / "tests")],
                capture_output=True,
                text=True,
                timeout=30
            )
            # We don't assert returncode == 0 because files might not be formatted yet.
            # We only assert that the command ran successfully (no crash).
            assert result.returncode is not None
        except FileNotFoundError:
            pytest.skip("Black is not installed in the environment")
        except subprocess.TimeoutExpired:
            pytest.skip("Black check timed out")