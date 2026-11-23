"""
Unit tests for linting and formatting configuration.
Verifies that configuration files exist and contain expected settings.
"""
import os
import pytest
from pathlib import Path
import tomli

class TestLintingConfig:
    """Tests for linting configuration files."""

    def test_ruff_toml_exists(self):
        """Test that ruff.toml configuration file exists."""
        ruff_path = Path("ruff.toml")
        assert ruff_path.exists(), "ruff.toml configuration file not found"

    def test_ruff_toml_valid_toml(self):
        """Test that ruff.toml is valid TOML."""
        ruff_path = Path("ruff.toml")
        with open(ruff_path, "rb") as f:
            try:
                config = tomli.load(f)
            except Exception as e:
                pytest.fail(f"ruff.toml is not valid TOML: {e}")
        
        # Verify essential keys exist
        assert "line-length" in config, "ruff.toml missing 'line-length'"
        assert config["line-length"] == 88, "ruff.toml line-length should be 88"

    def test_pyproject_toml_black_config(self):
        """Test that pyproject.toml contains Black configuration."""
        pyproject_path = Path("pyproject.toml")
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        assert "tool" in config, "pyproject.toml missing [tool] section"
        assert "black" in config["tool"], "pyproject.toml missing [tool.black] section"
        assert config["tool"]["black"]["line-length"] == 88, "Black line-length should be 88"

    def test_pyproject_toml_isort_config(self):
        """Test that pyproject.toml contains isort configuration."""
        pyproject_path = Path("pyproject.toml")
        
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        assert "isort" in config["tool"], "pyproject.toml missing [tool.isort] section"
        assert config["tool"]["isort"]["profile"] == "black", "isort profile should be 'black'"

    def test_linting_tools_installed(self):
        """Test that linting tools are installed and accessible."""
        import subprocess
        import sys

        tools = ["flake8", "pylint", "black", "isort"]
        for tool in tools:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", tool],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"{tool} is not installed"

    def test_config_files_in_project_root(self):
        """Test that configuration files are in the project root."""
        expected_files = ["ruff.toml", "pyproject.toml"]
        for filename in expected_files:
            path = Path(filename)
            assert path.exists(), f"{filename} not found in project root"
            # Verify it's in the root, not in a subdirectory
            assert path.parent == Path("."), f"{filename} should be in project root"
