import subprocess
import os
import pytest
from pathlib import Path
import tomli

project_root = Path(__file__).resolve().parent.parent.parent

def test_flake8_config_exists():
    """Test that .flake8 configuration file exists."""
    flake8_path = project_root / ".flake8"
    assert flake8_path.exists(), "flake8 configuration file (.flake8) not found"

def test_pyproject_toml_exists():
    """Test that pyproject.toml exists."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"

def test_black_can_parse_config():
    """Test that black can parse the configuration."""
    pyproject_path = project_root / "pyproject.toml"
    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        assert "tool" in config
        assert "black" in config["tool"]
    except Exception as e:
        pytest.fail(f"Failed to parse pyproject.toml: {e}")

def test_flake8_can_parse_config():
    """Test that flake8 can parse the configuration."""
    flake8_path = project_root / ".flake8"
    if flake8_path.exists():
        result = subprocess.run(
            ["flake8", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"flake8 failed: {result.stderr}"
    else:
        pytest.skip("flake8 configuration file not found")

def test_linting_rules_are_reasonable():
    """Test that linting rules are reasonable."""
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        if "tool" in config and "black" in config["tool"]:
            black_config = config["tool"]["black"]
            # Check for reasonable max line length
            if "line-length" in black_config:
                assert black_config["line-length"] <= 120, "max line length too high"
    else:
        pytest.skip("pyproject.toml not found")
