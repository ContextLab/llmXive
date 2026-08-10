"""
Unit tests to verify linting configuration files exist and are valid.
"""
import os
import subprocess
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class TestLintingConfig:
    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists and contains black/isort config."""
        path = ROOT_DIR / "pyproject.toml"
        assert path.exists(), "pyproject.toml must exist"
        content = path.read_text()
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        assert "[tool.isort]" in content, "pyproject.toml must contain [tool.isort] section"

    def test_flake8_config_exists(self):
        """Test that .flake8 config file exists."""
        path = ROOT_DIR / ".flake8"
        assert path.exists(), ".flake8 must exist"
        content = path.read_text()
        assert "[flake8]" in content, ".flake8 must contain [flake8] section"

    def test_isort_config_exists(self):
        """Test that .isort.cfg config file exists."""
        path = ROOT_DIR / ".isort.cfg"
        assert path.exists(), ".isort.cfg must exist"
        content = path.read_text()
        assert "[settings]" in content, ".isort.cfg must contain [settings] section"

    def test_black_is_available(self):
        """Test that black command is available."""
        result = subprocess.run(["black", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "black must be installed and available"
        assert "black" in result.stdout.lower(), "Output should mention black"

    def test_flake8_is_available(self):
        """Test that flake8 command is available."""
        result = subprocess.run(["flake8", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "flake8 must be installed and available"
        assert "flake8" in result.stdout.lower(), "Output should mention flake8"

    def test_isort_is_available(self):
        """Test that isort command is available."""
        result = subprocess.run(["isort", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "isort must be installed and available"
        assert "isort" in result.stdout.lower(), "Output should mention isort"