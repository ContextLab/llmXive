"""
Unit tests to verify linting configuration files exist and are valid.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def test_flake8_config_exists():
    """Verify .flake8 configuration file exists."""
    config_path = PROJECT_ROOT / ".flake8"
    assert config_path.exists(), ".flake8 configuration file is missing"
    assert config_path.stat().st_size > 0, ".flake8 file is empty"

def test_pyproject_toml_exists():
    """Verify pyproject.toml configuration file exists."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    assert config_path.exists(), "pyproject.toml configuration file is missing"
    assert config_path.stat().st_size > 0, "pyproject.toml file is empty"

def test_black_config_valid():
    """Verify Black configuration is present and valid in pyproject.toml."""
    config_path = PROJECT_ROOT / "pyproject.toml"
    try:
        with open(config_path, "r") as f:
            config = toml.load(f)
        
        assert "tool" in config, "No [tool] section in pyproject.toml"
        assert "black" in config["tool"], "No [tool.black] section found"
        
        black_config = config["tool"]["black"]
        assert "line-length" in black_config, "line-length not configured for Black"
        assert black_config["line-length"] == 88, f"Expected line-length 88, got {black_config['line-length']}"
    except Exception as e:
        pytest.fail(f"Failed to validate Black configuration: {e}")

def test_flake8_config_valid():
    """Verify .flake8 configuration is present and valid."""
    config_path = PROJECT_ROOT / ".flake8"
    try:
        with open(config_path, "r") as f:
            content = f.read()
        
        assert "[flake8]" in content, "No [flake8] section found in .flake8"
        assert "max-line-length" in content, "max-line-length not configured in .flake8"
    except Exception as e:
        pytest.fail(f"Failed to validate Flake8 configuration: {e}")

def test_gitignore_excludes_data_raw():
    """Verify .gitignore ignores data/raw and data/intermediate."""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.exists(), ".gitignore file is missing"
    
    with open(gitignore_path, "r") as f:
        content = f.read()
    
    assert "data/raw/" in content, ".gitignore should ignore data/raw/"
    assert "data/intermediate/" in content, ".gitignore should ignore data/intermediate/"
    assert "data/ownership_metrics/" not in content or "!data/ownership_metrics/*.csv" in content, \
        ".gitignore should not ignore ownership_metrics CSVs"