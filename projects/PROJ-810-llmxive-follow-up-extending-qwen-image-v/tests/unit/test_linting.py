"""
Unit tests for linting and formatting configuration.
Verifies that configuration files are valid and tools work correctly.
"""
import os
import subprocess
from pathlib import Path
import pytest


class TestLintingConfiguration:
    """Test suite for linting configuration files."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent

    def test_pyproject_toml_exists(self, project_root):
        """Verify pyproject.toml exists."""
        config_path = project_root / "pyproject.toml"
        assert config_path.exists(), "pyproject.toml not found"

    def test_pyproject_toml_valid(self, project_root):
        """Verify pyproject.toml is valid TOML."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        config_path = project_root / "pyproject.toml"
        with open(config_path, "rb") as f:
            config = tomllib.load(f)

        assert "tool" in config
        assert "black" in config["tool"]
        assert "ruff" in config["tool"]

    def test_ruff_toml_exists(self, project_root):
        """Verify .ruff.toml exists."""
        config_path = project_root / ".ruff.toml"
        assert config_path.exists(), ".ruff.toml not found"

    def test_flake8_config_exists(self, project_root):
        """Verify .flake8 exists."""
        config_path = project_root / ".flake8"
        assert config_path.exists(), ".flake8 not found"

    def test_ruff_version_available(self):
        """Verify ruff is installed and accessible."""
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "ruff not installed or not in PATH"
        assert "ruff" in result.stdout.lower()

    def test_black_version_available(self):
        """Verify black is installed and accessible."""
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "black not installed or not in PATH"
        assert "black" in result.stdout.lower()

    def test_setup_linting_script_exists(self, project_root):
        """Verify setup_linting.py exists."""
        script_path = project_root / "setup_linting.py"
        assert script_path.exists(), "setup_linting.py not found"

    def test_setup_linting_script_importable(self, project_root):
        """Verify setup_linting.py can be imported."""
        sys.path.insert(0, str(project_root))
        try:
            import setup_linting
            assert hasattr(setup_linting, "check_tool_installed")
            assert hasattr(setup_linting, "install_tools")
            assert hasattr(setup_linting, "main")
        finally:
            sys.path.pop(0)