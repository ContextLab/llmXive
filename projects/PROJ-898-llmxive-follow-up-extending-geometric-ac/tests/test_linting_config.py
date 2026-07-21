"""
Test suite to verify linting and formatting configurations are valid.
This ensures T003 (Configure linting and formatting) is correctly set up.
"""
import subprocess
import sys
import os
import tempfile
import pytest

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    # Check root config
    assert os.path.exists(".ruff.toml"), "Root .ruff.toml file missing"
    # Check code-specific config
    assert os.path.exists("code/.ruff.toml"), "code/.ruff.toml file missing"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists with black configuration."""
    assert os.path.exists("pyproject.toml"), "pyproject.toml file missing"

def test_ruff_can_run():
    """Verify ruff can be executed and finds no critical errors in config."""
    # Run ruff check on the test file itself to ensure it works
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", __file__],
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect success (0) or warnings (non-zero but valid run)
        # The important thing is the command runs without crashing
        assert result.returncode in [0, 1], f"Ruff check failed unexpectedly: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")

def test_black_can_run():
    """Verify black can be executed."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", __file__],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black returns 0 if file is formatted correctly, 1 if not
        # We just verify it runs without crashing
        assert result.returncode in [0, 1], f"Black check failed unexpectedly: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")

def test_config_syntax_valid():
    """Verify configuration files have valid TOML syntax."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            pytest.skip("tomllib/tomli not available")

    with open("pyproject.toml", "rb") as f:
        tomllib.load(f)
    
    # .ruff.toml is also TOML
    with open(".ruff.toml", "rb") as f:
        tomllib.load(f)