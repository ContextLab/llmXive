import os
import toml
import configparser
import pytest
from pathlib import Path

# Determine the project root (assuming tests are in tests/unit/ and artifacts in code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"

def test_flake8_config_exists():
    """Verify .flake8 file exists in code directory."""
    flake8_path = CODE_DIR / ".flake8"
    assert flake8_path.exists(), f".flake8 file not found at {flake8_path}"

def test_flake8_config_content():
    """Verify .flake8 contains correct max-line-length."""
    flake8_path = CODE_DIR / ".flake8"
    config = configparser.ConfigParser()
    config.read(flake8_path)

    assert "flake8" in config, "Missing [flake8] section in .flake8"
    assert "max-line-length" in config["flake8"], "Missing max-line-length in [flake8]"
    assert int(config["flake8"]["max-line-length"]) == 88, "max-line-length should be 88"

def test_pyproject_toml_exists():
    """Verify pyproject.toml file exists in code directory."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml file not found at {pyproject_path}"

def test_pyproject_toml_black_config():
    """Verify pyproject.toml contains correct black configuration."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    
    with open(pyproject_path, "r") as f:
        content = f.read()
    
    # Check for [tool.black] section
    assert "[tool.black]" in content, "Missing [tool.black] section in pyproject.toml"
    
    # Parse toml to ensure validity
    data = toml.load(pyproject_path)
    assert "tool" in data, "Missing 'tool' key in pyproject.toml"
    assert "black" in data["tool"], "Missing 'black' key under 'tool'"
    assert data["tool"]["black"]["line-length"] == 88, "line-length should be 88"