"""
Unit tests to verify that linting and formatting configuration files exist and are valid.
"""
import os
from pathlib import Path

def test_ruff_config_exists():
    """Test that .ruff.toml exists in the code directory."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    config_path = code_dir / ".ruff.toml"
    assert config_path.exists(), f"Ruff config missing at {config_path}"

def test_black_config_exists():
    """Test that .black.toml exists in the code directory."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    config_path = code_dir / ".black.toml"
    assert config_path.exists(), f"Black config missing at {config_path}"

def test_ruff_config_valid_toml():
    """Test that .ruff.toml is valid TOML."""
    import tomllib
    code_dir = Path(__file__).parent.parent.parent / "code"
    config_path = code_dir / ".ruff.toml"
    with open(config_path, "rb") as f:
        try:
            tomllib.load(f)
        except Exception as e:
            assert False, f"Invalid TOML in .ruff.toml: {e}"

def test_black_config_valid_toml():
    """Test that .black.toml is valid TOML."""
    import tomllib
    code_dir = Path(__file__).parent.parent.parent / "code"
    config_path = code_dir / ".black.toml"
    with open(config_path, "rb") as f:
        try:
            tomllib.load(f)
        except Exception as e:
            assert False, f"Invalid TOML in .black.toml: {e}"
