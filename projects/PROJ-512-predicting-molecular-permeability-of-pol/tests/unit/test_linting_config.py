"""
Unit tests to verify that linting and formatting configurations are present and valid.
These tests check for the existence of configuration files and basic syntax validity.
"""
import os
import subprocess
import tempfile
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in project root."""
    config_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    assert os.path.isfile(config_path), "pyproject.toml not found in project root"

def test_pyproject_toml_contains_black():
    """Verify pyproject.toml contains Black configuration."""
    config_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    with open(config_path, "r") as f:
        content = f.read()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length" in content, "Black line-length setting missing"

def test_pyproject_toml_contains_ruff():
    """Verify pyproject.toml contains Ruff configuration."""
    config_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    with open(config_path, "r") as f:
        content = f.read()
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
    assert "select" in content, "Ruff lint rules selection missing"

def test_ruff_config_valid_syntax():
    """Verify ruff configuration does not crash on basic parse."""
    # We run ruff check on the config file itself to ensure it's recognized
    # If ruff is installed, this should pass. If not, we skip.
    try:
        result = subprocess.run(
            ["ruff", "check", "--isolated", PROJECT_ROOT],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # If ruff is available, it should at least parse the config without error code 2 (config error)
        # Code 1 means lint errors found, which is fine for this test.
        # Code 2 means config error.
        assert result.returncode != 2, f"Ruff config error: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")

def test_black_config_valid_syntax():
    """Verify black configuration does not crash on basic parse."""
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", "--config", os.path.join(PROJECT_ROOT, "pyproject.toml"), PROJECT_ROOT],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black returns 0 if everything is formatted, 1 if not.
        # It returns 2 if there is a config error.
        assert result.returncode != 2, f"Black config error: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")