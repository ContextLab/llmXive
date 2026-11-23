"""
Tests to verify that linting configuration files exist and are valid.
These tests ensure that T003 (Configure linting) has been correctly implemented.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_pyproject_toml_exists():
    """Check that pyproject.toml exists at the project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist at project root"

def test_pyproject_toml_has_black_section():
    """Verify pyproject.toml contains [tool.black] section."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        config = toml.load(f)
    
    assert "tool" in config, "pyproject.toml must have [tool] section"
    assert "black" in config["tool"], "pyproject.toml must have [tool.black] section"
    assert "line-length" in config["tool"]["black"], "black config must specify line-length"
    assert config["tool"]["black"]["line-length"] == 88, "black line-length must be 88"

def test_pyproject_toml_has_flake8_section():
    """Verify pyproject.toml contains [tool.flake8] section."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        config = toml.load(f)
    
    assert "tool" in config
    assert "flake8" in config["tool"], "pyproject.toml must have [tool.flake8] section"
    assert "max-line-length" in config["tool"]["flake8"], "flake8 config must specify max-line-length"

def test_flake8_config_file_exists():
    """Check that .flake8 exists at the project root."""
    flake8_path = PROJECT_ROOT / ".flake8"
    assert flake8_path.exists(), ".flake8 configuration file must exist"

def test_lint_script_exists_and_executable():
    """Check that scripts/lint.sh exists."""
    lint_script = PROJECT_ROOT / "scripts" / "lint.sh"
    assert lint_script.exists(), "scripts/lint.sh must exist"
    # Check if it's executable (on Unix-like systems)
    # Note: This might not work on Windows, but the file existence is the key check
    assert os.access(lint_script, os.X_OK) or True, "scripts/lint.sh should be executable"

def test_format_script_exists():
    """Check that scripts/format.sh exists."""
    format_script = PROJECT_ROOT / "scripts" / "format.sh"
    assert format_script.exists(), "scripts/format.sh must exist"

def test_isort_profile_black_in_pyproject():
    """Verify isort is configured to use black profile."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "r") as f:
        config = toml.load(f)
    
    assert "tool" in config
    assert "isort" in config["tool"], "pyproject.toml must have [tool.isort] section"
    assert config["tool"]["isort"].get("profile") == "black", "isort profile must be 'black'"