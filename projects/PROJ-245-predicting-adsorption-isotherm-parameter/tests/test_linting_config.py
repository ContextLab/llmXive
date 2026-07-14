"""
Smoke test to verify that linting and formatting tools are correctly configured.
This test ensures that the project's configuration files exist and are valid.
"""
import os
import toml
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_black_config_exists():
    """Verify pyproject.toml contains Black configuration."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    config = toml.load(pyproject_path)
    assert "tool" in config
    assert "black" in config["tool"], "Black configuration missing in pyproject.toml"
    
    assert config["tool"]["black"]["line-length"] == 88
    assert "py311" in config["tool"]["black"]["target-version"]

def test_ruff_config_exists():
    """Verify .ruff.toml exists and is valid."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    assert ruff_path.exists(), ".ruff.toml not found"
    
    # Basic validation: file should not be empty
    content = ruff_path.read_text()
    assert len(content) > 50, ".ruff.toml appears to be empty or too short"
    assert "target-version" in content

def test_scripts_exist():
    """Verify helper scripts for formatting and linting exist."""
    format_script = PROJECT_ROOT / "scripts" / "format.sh"
    lint_script = PROJECT_ROOT / "scripts" / "lint.sh"
    
    assert format_script.exists(), "scripts/format.sh not found"
    assert lint_script.exists(), "scripts/lint.sh not found"
    
    # Check executability (on Unix-like systems)
    import stat
    assert os.access(format_script, os.X_OK) or format_script.stat().st_mode & stat.S_IXUSR
    assert os.access(lint_script, os.X_OK) or lint_script.stat().st_mode & stat.S_IXUSR

def test_pytest_config_exists():
    """Verify pytest configuration in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    config = toml.load(pyproject_path)
    
    assert "tool" in config
    assert "pytest" in config["tool"]
    assert "ini_options" in config["tool"]["pytest"]
    
    options = config["tool"]["pytest"]["ini_options"]
    assert "testpaths" in options
    assert "tests" in options["testpaths"]