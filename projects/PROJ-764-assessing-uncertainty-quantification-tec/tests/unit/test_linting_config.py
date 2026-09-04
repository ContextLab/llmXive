"""
Tests for linting and formatting configuration (T003).
Verifies that ruff and black configurations exist and are valid.
"""
import os
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"


def test_ruff_config_exists():
    """Test that ruff.toml exists in the code directory."""
    ruff_config = CODE_DIR / "ruff.toml"
    assert ruff_config.exists(), "ruff.toml configuration file is missing"
    assert ruff_config.stat().st_size > 0, "ruff.toml is empty"


def test_black_config_exists():
    """Test that black configuration exists in pyproject.toml."""
    pyproject = CODE_DIR / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml is missing"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"


def test_ruff_config_syntax_valid():
    """Test that ruff.toml has valid TOML syntax by attempting to parse it."""
    ruff_config = CODE_DIR / "ruff.toml"
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            pytest.skip("tomllib or tomli not available")

    with open(ruff_config, "rb") as f:
        tomllib.load(f)


def test_pyproject_toml_syntax_valid():
    """Test that pyproject.toml has valid TOML syntax."""
    pyproject = CODE_DIR / "pyproject.toml"
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            pytest.skip("tomllib or tomli not available")

    with open(pyproject, "rb") as f:
        tomllib.load(f)


def test_requirements_includes_dev_tools():
    """Test that requirements.txt includes ruff and black."""
    requirements = CODE_DIR / "requirements.txt"
    content = requirements.read_text()
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"