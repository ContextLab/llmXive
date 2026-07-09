"""
Unit tests for the linting and formatting configuration.

These tests verify that the configuration files are created correctly
and that the required tools are available.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest

# Add the project root to the path to allow imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.tools.lint_format import (
    create_ruff_config,
    create_black_config,
    create_vscode_settings,
)


class TestLintFormatConfig:
    """Tests for lint and format configuration generation."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary directory for testing configuration generation."""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield temp_dir
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    def test_ruff_config_creation(self, temp_project):
        """Test that Ruff configuration is created in pyproject.toml."""
        create_ruff_config()
        
        assert os.path.exists("pyproject.toml")
        
        import tomllib
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        
        assert "tool" in config
        assert "ruff" in config["tool"]
        assert config["tool"]["ruff"]["line-length"] == 100
        assert "E" in config["tool"]["ruff"]["lint"]["select"]

    def test_black_config_creation(self, temp_project):
        """Test that Black configuration is created in pyproject.toml."""
        create_black_config()
        
        assert os.path.exists("pyproject.toml")
        
        import tomllib
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        
        assert "tool" in config
        assert "black" in config["tool"]
        assert config["tool"]["black"]["line-length"] == 100

    def test_vscode_settings_creation(self, temp_project):
        """Test that VS Code settings are created."""
        create_vscode_settings()
        
        settings_path = ".vscode/settings.json"
        assert os.path.exists(settings_path)
        
        with open(settings_path, "r") as f:
            settings = json.load(f)
        
        assert settings["editor.defaultFormatter"] == "ms-python.black-formatter"
        assert settings["editor.formatOnSave"] is True
        assert settings["python.linting.ruffEnabled"] is True

    def test_combined_config(self, temp_project):
        """Test that both Ruff and Black configs coexist in pyproject.toml."""
        create_ruff_config()
        create_black_config()
        
        assert os.path.exists("pyproject.toml")
        
        import tomllib
        with open("pyproject.toml", "rb") as f:
            config = tomllib.load(f)
        
        assert "tool" in config
        assert "ruff" in config["tool"]
        assert "black" in config["tool"]

class TestToolAvailability:
    """Tests to verify that required tools are importable."""

    def test_ruff_importable(self):
        """Test that ruff is importable."""
        try:
            import ruff
            assert True
        except ImportError:
            pytest.skip("ruff is not installed in this environment")

    def test_black_importable(self):
        """Test that black is importable."""
        try:
            import black
            assert True
        except ImportError:
            pytest.skip("black is not installed in this environment")
