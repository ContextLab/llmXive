"""
Basic sanity checks for linting and formatting configuration.
These tests ensure that the configuration files exist and are valid TOML.
"""
import os
import tomllib
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"


def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    config_path = CODE_DIR / ".ruff.toml"
    assert config_path.exists(), f"Ruff config missing at {config_path}"


def test_black_config_exists():
    """Verify black configuration file exists."""
    config_path = CODE_DIR / ".black.toml"
    assert config_path.exists(), f"Black config missing at {config_path}"


def test_ruff_config_valid():
    """Verify ruff configuration is valid TOML."""
    config_path = CODE_DIR / ".ruff.toml"
    try:
        with open(config_path, "rb") as f:
            tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        pytest.fail(f"Invalid TOML in .ruff.toml: {e}")


def test_black_config_valid():
    """Verify black configuration is valid TOML."""
    config_path = CODE_DIR / ".black.toml"
    try:
        with open(config_path, "rb") as f:
            tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        pytest.fail(f"Invalid TOML in .black.toml: {e}")


def test_requirements_includes_linters():
    """Verify requirements.txt includes ruff and black."""
    req_path = PROJECT_ROOT / "requirements.txt"
    assert req_path.exists(), "requirements.txt missing"

    with open(req_path, "r") as f:
        content = f.read().lower()

    assert "ruff" in content, "ruff missing from requirements.txt"
    assert "black" in content, "black missing from requirements.txt"