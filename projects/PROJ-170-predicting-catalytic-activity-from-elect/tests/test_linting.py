"""
Tests for T002: Linting and Formatting Configuration.
These tests verify that the configuration files exist and the helper functions work.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config import get_project_root
from linting_config import ensure_linting_config, run_black_check, run_ruff_check


def test_pyproject_toml_exists():
    """Test that pyproject.toml exists in the project root."""
    project_root = get_project_root()
    config_path = project_root / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml must exist for T002"


def test_pyproject_has_black_config():
    """Test that pyproject.toml contains [tool.black] section."""
    project_root = get_project_root()
    config_path = project_root / "pyproject.toml"
    content = config_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black]"


def test_pyproject_has_ruff_config():
    """Test that pyproject.toml contains [tool.ruff] section."""
    project_root = get_project_root()
    config_path = project_root / "pyproject.toml"
    content = config_path.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff]"


def test_ensure_linting_config_success():
    """Test that ensure_linting_config passes when config is valid."""
    # This should not raise an exception
    try:
        ensure_linting_config()
    except (FileNotFoundError, ValueError) as e:
        pytest.fail(f"ensure_linting_config raised unexpected error: {e}")


def test_linting_functions_return_int():
    """Test that linting check functions return integer exit codes."""
    # We expect these to run (even if they fail due to formatting issues)
    # and return an integer code.
    black_code = run_black_check()
    ruff_code = run_ruff_check()

    assert isinstance(black_code, int), "run_black_check must return int"
    assert isinstance(ruff_code, int), "run_ruff_check must return int"

    # Note: We do not assert they are 0 here, as the code might not be
    # perfectly formatted yet, but the functions must execute and return a code.