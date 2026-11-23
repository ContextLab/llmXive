"""
Smoke test to verify linting configuration files exist and are valid.
This ensures the environment is ready for CI/CD linting steps.
"""
import os
import tomllib
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    path = os.path.join(CODE_DIR, ".ruff.toml")
    assert os.path.exists(path), f"Ruff config missing at {path}"

def test_ruff_config_valid():
    """Verify ruff configuration is valid TOML."""
    path = os.path.join(CODE_DIR, ".ruff.toml")
    with open(path, "rb") as f:
        try:
            tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

def test_black_config_exists():
    """Verify black configuration file exists."""
    path = os.path.join(CODE_DIR, ".black.toml")
    assert os.path.exists(path), f"Black config missing at {path}"

def test_black_config_valid():
    """Verify black configuration is valid TOML."""
    path = os.path.join(CODE_DIR, ".black.toml")
    with open(path, "rb") as f:
        try:
            tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"Invalid TOML in .black.toml: {e}")