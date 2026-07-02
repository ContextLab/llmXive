"""
Tests for linting configuration and utilities.
"""
import pytest
from pathlib import Path
import sys
import subprocess

class TestLintingConfig:
    """Test suite for linting configuration and utilities."""

    def test_flake8_import(self):
        """Test that run_flake8 can be imported from linting_config."""
        try:
            from linting_config import run_flake8
            assert callable(run_flake8)
        except ImportError as e:
            pytest.fail(f"Failed to import run_flake8: {e}")

    def test_black_import(self):
        """Test that run_black can be imported from linting_config."""
        try:
            from linting_config import run_black
            assert callable(run_black)
        except ImportError as e:
            pytest.fail(f"Failed to import run_black: {e}")

    def test_isort_import(self):
        """Test that run_isort can be imported from linting_config."""
        try:
            from linting_config import run_isort
            assert callable(run_isort)
        except ImportError as e:
            pytest.fail(f"Failed to import run_isort: {e}")

    def test_run_all_checks_import(self):
        """Test that run_all_checks can be imported from linting_config."""
        try:
            from linting_config import run_all_checks
            assert callable(run_all_checks)
        except ImportError as e:
            pytest.fail(f"Failed to import run_all_checks: {e}")

    def test_run_all_formatters_import(self):
        """Test that run_all_formatters can be imported from linting_config."""
        try:
            from linting_config import run_all_formatters
            assert callable(run_all_formatters)
        except ImportError as e:
            pytest.fail(f"Failed to import run_all_formatters: {e}")

    def test_config_files_exist(self):
        """Test that required configuration files exist."""
        config_files = [
            "setup.cfg",
            "pyproject.toml"
        ]
        
        for config_file in config_files:
            config_path = Path.cwd() / config_file
            assert config_path.exists(), f"Configuration file {config_file} not found"

    def test_flake8_config_present(self):
        """Test that flake8 configuration is present in setup.cfg."""
        setup_cfg = Path.cwd() / "setup.cfg"
        assert setup_cfg.exists(), "setup.cfg not found"
        
        content = setup_cfg.read_text()
        assert "[flake8]" in content, "flake8 configuration not found in setup.cfg"

    def test_black_config_present(self):
        """Test that black configuration is present in pyproject.toml."""
        pyproject = Path.cwd() / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml not found"
        
        content = pyproject.read_text()
        assert "[tool.black]" in content, "black configuration not found in pyproject.toml"

    def test_isort_config_present(self):
        """Test that isort configuration is present in pyproject.toml."""
        pyproject = Path.cwd() / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml not found"
        
        content = pyproject.read_text()
        assert "[tool.isort]" in content, "isort configuration not found in pyproject.toml"