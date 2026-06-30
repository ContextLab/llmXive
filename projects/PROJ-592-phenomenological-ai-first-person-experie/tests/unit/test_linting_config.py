"""
Tests to verify that linting and formatting configuration files exist and are valid.
These tests ensure that the project is set up for consistent code style.
"""
import os
import toml
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE_DIR = os.path.join(PROJECT_ROOT, "code")

def test_ruff_config_exists():
    """Test that .ruff.toml exists in the code directory."""
    config_path = os.path.join(CODE_DIR, ".ruff.toml")
    assert os.path.exists(config_path), f"Ruff config not found at {config_path}"

def test_ruff_config_valid():
    """Test that .ruff.toml is valid TOML and contains expected sections."""
    config_path = os.path.join(CODE_DIR, ".ruff.toml")
    try:
        config = toml.load(config_path)
        assert "lint" in config, "Ruff config missing 'lint' section"
        assert "format" in config, "Ruff config missing 'format' section"
        assert config["lint"]["target-version"] == "py311"
    except Exception as e:
        pytest.fail(f"Invalid Ruff config: {e}")

def test_black_config_exists():
    """Test that .black.toml exists in the code directory."""
    config_path = os.path.join(CODE_DIR, ".black.toml")
    assert os.path.exists(config_path), f"Black config not found at {config_path}"

def test_black_config_valid():
    """Test that .black.toml is valid TOML and contains expected settings."""
    config_path = os.path.join(CODE_DIR, ".black.toml")
    try:
        config = toml.load(config_path)
        assert "tool" in config, "Black config missing 'tool' section"
        assert "black" in config["tool"], "Black config missing 'black' section"
        assert config["tool"]["black"]["target-version"] == ['py311']
        assert config["tool"]["black"]["line-length"] == 88
    except Exception as e:
        pytest.fail(f"Invalid Black config: {e}")

def test_setup_script_exists():
    """Test that setup_linting.sh exists."""
    script_path = os.path.join(CODE_DIR, "scripts", "setup_linting.sh")
    assert os.path.exists(script_path), f"Setup script not found at {script_path}"

def test_setup_script_executable():
    """Test that setup_linting.sh has executable permissions."""
    script_path = os.path.join(CODE_DIR, "scripts", "setup_linting.sh")
    assert os.access(script_path, os.X_OK), f"Setup script is not executable: {script_path}"