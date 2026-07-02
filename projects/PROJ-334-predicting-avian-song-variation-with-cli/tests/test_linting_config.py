"""
Tests for linting configuration setup.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# Since the file is in code/, we need to ensure the path is correct
# Assuming the test runs from the project root or the path is handled
import sys
import importlib.util

# Dynamically load the module to avoid path issues during testing
spec = importlib.util.spec_from_file_location(
    "linting_config", "code/linting_config.py"
)
linting_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(linting_config)


def test_config_files_exist_after_generation(tmp_path):
    """Test that configuration files are created when they don't exist."""
    # Temporarily override PROJECT_ROOT for this test
    original_root = linting_config.PROJECT_ROOT
    linting_config.PROJECT_ROOT = tmp_path

    try:
        # Call the function to write configs
        linting_config.write_config_files()

        # Check that files were created
        pyproject = tmp_path / "pyproject.toml"
        flake8_cfg = tmp_path / ".flake8"

        assert pyproject.exists(), "pyproject.toml should be created"
        assert flake8_cfg.exists(), ".flake8 should be created"

        # Verify content contains expected keys
        pyproject_content = pyproject.read_text()
        assert "tool.black" in pyproject_content, "pyproject.toml should contain [tool.black]"
        assert "line-length" in pyproject_content, "pyproject.toml should contain line-length"

        flake8_content = flake8_cfg.read_text()
        assert "max-line-length" in flake8_content, ".flake8 should contain max-line-length"
    finally:
        # Restore original root
        linting_config.PROJECT_ROOT = original_root


def test_config_files_not_overwritten(tmp_path):
    """Test that existing config files are not overwritten."""
    # Temporarily override PROJECT_ROOT
    original_root = linting_config.PROJECT_ROOT
    linting_config.PROJECT_ROOT = tmp_path

    try:
        # Create dummy files first
        pyproject = tmp_path / "pyproject.toml"
        flake8_cfg = tmp_path / ".flake8"
        pyproject.write_text("[existing]\ncontent=1")
        flake8_cfg.write_text("[existing]\ncontent=2")

        # Call the function
        linting_config.write_config_files()

        # Verify content is unchanged
        assert pyproject.read_text() == "[existing]\ncontent=1"
        assert flake8_cfg.read_text() == "[existing]\ncontent=2"
    finally:
        linting_config.PROJECT_ROOT = original_root


def test_main_function_runs_without_error(tmp_path):
    """Test that the main function runs without raising exceptions."""
    original_root = linting_config.PROJECT_ROOT
    linting_config.PROJECT_ROOT = tmp_path

    try:
        # This should not raise
        linting_config.main()
        assert True
    except Exception as e:
        pytest.fail(f"main() raised an exception: {e}")
    finally:
        linting_config.PROJECT_ROOT = original_root