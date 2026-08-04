import os
import tomli
import pytest
from pathlib import Path

# Ensure we can import from the code root
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

ROOT_DIR = Path(__file__).parent.parent.parent.parent

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at the project root."""
    assert (ROOT_DIR / "pyproject.toml").exists(), "pyproject.toml must exist at project root"

def test_pyproject_toml_has_black_config():
    """Verify black configuration is present in pyproject.toml."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    assert pyproject_path.exists()
    
    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config, "tool section missing"
    assert "black" in config["tool"], "black configuration missing in [tool.black]"
    
    black_config = config["tool"]["black"]
    assert "line-length" in black_config, "black line-length not configured"
    assert black_config["line-length"] == 88, f"Expected line-length 88, got {black_config['line-length']}"

def test_pyproject_toml_has_ruff_config():
    """Verify ruff configuration is present in pyproject.toml."""
    pyproject_path = ROOT_DIR / "pyproject.toml"
    assert pyproject_path.exists()
    
    with open(pyproject_path, "rb") as f:
        config = tomli.load(f)
    
    assert "tool" in config, "tool section missing"
    assert "ruff" in config["tool"], "ruff configuration missing in [tool.ruff]"
    
    ruff_config = config["tool"]["ruff"]
    assert "line-length" in ruff_config, "ruff line-length not configured"
    assert ruff_config["line-length"] == 88, f"Expected line-length 88, got {ruff_config['line-length']}"

def test_flake8_config_exists():
    """Verify .flake8 config file exists."""
    assert (ROOT_DIR / ".flake8").exists(), ".flake8 config must exist at project root"

def test_flake8_config_valid():
    """Verify .flake8 config has valid syntax and required settings."""
    flake8_path = ROOT_DIR / ".flake8"
    assert flake8_path.exists()
    
    content = flake8_path.read_text()
    assert "[flake8]" in content, ".flake8 must have [flake8] section"
    assert "max-line-length" in content, "max-line-length must be configured in .flake8"
    assert "88" in content, "max-line-length should be 88 to match black"

def test_ruff_binary_available():
    """Verify ruff binary is available in PATH."""
    import shutil
    assert shutil.which("ruff") is not None, "ruff binary must be available in PATH"

def test_black_binary_available():
    """Verify black binary is available in PATH."""
    import shutil
    assert shutil.which("black") is not None, "black binary must be available in PATH"