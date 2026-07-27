"""
Unit tests to verify that linting and formatting configurations are present and valid.
"""
import os
from pathlib import Path
import pytest

def test_ruff_config_exists():
    """Test that .ruff.toml exists in the code directory."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    ruff_config = code_dir / ".ruff.toml"
    assert ruff_config.exists(), f"Ruff config file not found at {ruff_config}"

def test_black_config_exists():
    """Test that .black.toml exists in the code directory."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    black_config = code_dir / ".black.toml"
    assert black_config.exists(), f"Black config file not found at {black_config}"

def test_ruff_config_syntax():
    """Test that .ruff.toml is valid TOML (basic check)."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    ruff_config = code_dir / ".ruff.toml"
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            pytest.skip("tomllib or tomli not installed")

    with open(ruff_config, "rb") as f:
        try:
            tomllib.load(f)
        except Exception as e:
            pytest.fail(f"Invalid TOML in .ruff.toml: {e}")

def test_black_config_syntax():
    """Test that .black.toml is valid TOML (basic check)."""
    code_dir = Path(__file__).parent.parent.parent / "code"
    black_config = code_dir / ".black.toml"
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            pytest.skip("tomllib or tomli not installed")

    with open(black_config, "rb") as f:
        try:
            tomllib.load(f)
        except Exception as e:
            pytest.fail(f"Invalid TOML in .black.toml: {e}")