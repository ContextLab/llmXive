"""
Unit tests to verify linting and formatting configuration.
These tests ensure that pyproject.toml, .flake8, and ruff configurations
are correctly set up as per T003.
"""
import os
import tomli
import pytest
from pathlib import Path
import sys
import subprocess

# Add code directory to path for imports if needed, though this test mostly checks files
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PROJECT_ROOT = Path(__file__).parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
FLAKE8_PATH = PROJECT_ROOT / ".flake8"


def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists in the project root."""
    assert PYPROJECT_PATH.exists(), f"pyproject.toml not found at {PYPROJECT_PATH}"


def test_pyproject_toml_has_black_config():
    """Verify that pyproject.toml contains [tool.black] section with line-length=88."""
    if not PYPROJECT_PATH.exists():
        pytest.skip("pyproject.toml does not exist")

    with open(PYPROJECT_PATH, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "black" in config["tool"], "Missing [tool.black] section in pyproject.toml"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "Missing line-length in [tool.black]"
    assert black_config["line-length"] == 88, f"Expected line-length 88, got {black_config['line-length']}"


def test_pyproject_toml_has_ruff_config():
    """Verify that pyproject.toml contains [tool.ruff] section with required rules."""
    if not PYPROJECT_PATH.exists():
        pytest.skip("pyproject.toml does not exist")

    with open(PYPROJECT_PATH, "rb") as f:
        config = tomli.load(f)

    assert "tool" in config, "Missing [tool] section in pyproject.toml"
    assert "ruff" in config["tool"], "Missing [tool.ruff] section in pyproject.toml"
    
    ruff_config = config["tool"]["ruff"]
    
    # Check line-length
    assert "line-length" in ruff_config, "Missing line-length in [tool.ruff]"
    assert ruff_config["line-length"] == 88, f"Expected line-length 88, got {ruff_config['line-length']}"
    
    # Check lint rules
    assert "lint" in ruff_config, "Missing [tool.ruff.lint] section"
    lint_config = ruff_config["lint"]
    assert "select" in lint_config, "Missing 'select' in [tool.ruff.lint]"
    select_rules = lint_config["select"]
    
    # Verify E, W, F, I are present
    assert "E" in select_rules, "Missing 'E' (pycodestyle errors) in ruff select"
    assert "W" in select_rules, "Missing 'W' (pycodestyle warnings) in ruff select"
    assert "F" in select_rules, "Missing 'F' (Pyflakes) in ruff select"
    assert "I" in select_rules, "Missing 'I' (isort) in ruff select"


def test_flake8_config_exists():
    """Verify that .flake8 configuration file exists."""
    assert FLAKE8_PATH.exists(), f".flake8 not found at {FLAKE8_PATH}"


def test_flake8_config_valid():
    """Verify that .flake8 file contains valid configuration with max-line-length=88."""
    if not FLAKE8_PATH.exists():
        pytest.skip(".flake8 does not exist")

    content = FLAKE8_PATH.read_text()
    assert "[flake8]" in content, "Missing [flake8] section in .flake8"
    assert "max-line-length = 88" in content, "Missing or incorrect max-line-length in .flake8"


def test_ruff_binary_available():
    """Verify that ruff is installed and available."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"ruff command failed: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("ruff binary not found. Please install it: pip install ruff")
    except subprocess.TimeoutExpired:
        pytest.fail("ruff version check timed out")


def test_black_binary_available():
    """Verify that black is installed and available."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"black command failed: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("black binary not found. Please install it: pip install black")
    except subprocess.TimeoutExpired:
        pytest.fail("black version check timed out")