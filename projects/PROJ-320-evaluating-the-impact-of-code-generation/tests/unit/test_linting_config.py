"""
Unit tests to verify linting and formatting configuration files exist and are valid.
These tests ensure that T003 (Configure linting and formatting tools) is satisfied.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

def test_pyproject_toml_exists():
    """Assert that pyproject.toml exists at the project root."""
    assert PYPROJECT_PATH.exists(), "pyproject.toml must exist at project root"

def test_pyproject_toml_is_valid():
    """Assert that pyproject.toml is valid TOML and can be parsed."""
    try:
        with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
            data = toml.load(f)
        assert isinstance(data, dict), "pyproject.toml must be a valid TOML document"
    except Exception as e:
        pytest.fail(f"pyproject.toml is not valid TOML: {e}")

def test_black_section_exists():
    """Assert that [tool.black] section exists in pyproject.toml."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    assert "tool" in data, "Missing [tool] section"
    assert "black" in data["tool"], "Missing [tool.black] section"

def test_black_line_length_configured():
    """Assert that black line-length is configured (should match project standard)."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    black_config = data["tool"]["black"]
    assert "line-length" in black_config, "black line-length must be configured"
    assert black_config["line-length"] == 100, "black line-length should be 100"

def test_ruff_section_exists():
    """Assert that [tool.ruff] section exists in pyproject.toml."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    assert "tool" in data, "Missing [tool] section"
    assert "ruff" in data["tool"], "Missing [tool.ruff] section"

def test_ruff_lint_section_exists():
    """Assert that [tool.ruff.lint] section exists in pyproject.toml."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    assert "tool" in data, "Missing [tool] section"
    assert "ruff" in data["tool"], "Missing [tool.ruff] section"
    assert "lint" in data["tool"]["ruff"], "Missing [tool.ruff.lint] section"

def test_ruff_select_rules():
    """Assert that ruff selects standard error codes (E, W, F)."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    lint_config = data["tool"]["ruff"]["lint"]
    assert "select" in lint_config, "ruff must have 'select' configuration"
    selected = lint_config["select"]
    assert "E" in selected, "ruff must select E (pycodestyle errors)"
    assert "W" in selected, "ruff must select W (pycodestyle warnings)"
    assert "F" in selected, "ruff must select F (Pyflakes)"

def test_pytest_section_exists():
    """Assert that [tool.pytest.ini_options] exists."""
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        data = toml.load(f)
    assert "tool" in data, "Missing [tool] section"
    assert "pytest" in data["tool"], "Missing [tool.pytest] section"
    assert "ini_options" in data["tool"]["pytest"], "Missing [tool.pytest.ini_options]"