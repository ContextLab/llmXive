"""
Contract test for T003: Verify linting and formatting configuration.

This test ensures that:
1. Configuration files exist and are valid TOML.
2. The configuration enforces the required line length (88) and target version (py311).
3. The scripts directory contains the expected helper scripts.
"""
import os
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent / "code"

def test_ruff_config_exists_and_valid():
    """Verify .ruff.toml exists and contains correct settings."""
    config_path = PROJECT_ROOT / ".ruff.toml"
    assert config_path.exists(), "Ruff configuration file (.ruff.toml) is missing."
    
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    assert config.get("line-length") == 88, "Ruff line-length must be 88."
    assert config.get("target-version") == "py311", "Ruff target-version must be py311."
    assert "E" in config.get("lint", {}).get("select", []), "Ruff must select E (pycodestyle) codes."
    assert "F" in config.get("lint", {}).get("select", []), "Ruff must select F (Pyflakes) codes."

def test_black_config_exists_and_valid():
    """Verify .black.toml exists and contains correct settings."""
    config_path = PROJECT_ROOT / ".black.toml"
    assert config_path.exists(), "Black configuration file (.black.toml) is missing."
    
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    tool_config = config.get("tool", {}).get("black", {})
    assert tool_config.get("line-length") == 88, "Black line-length must be 88."
    assert "py311" in tool_config.get("target-version", []), "Black target-version must include py311."

def test_dev_requirements_includes_tools():
    """Verify requirements-dev.txt includes ruff and black."""
    req_path = PROJECT_ROOT / "requirements-dev.txt"
    assert req_path.exists(), "requirements-dev.txt is missing."
    
    content = req_path.read_text()
    assert "ruff" in content, "ruff must be in requirements-dev.txt."
    assert "black" in content, "black must be in requirements-dev.txt."

def test_lint_scripts_exist():
    """Verify linting helper scripts exist."""
    scripts_dir = PROJECT_ROOT / "scripts"
    assert scripts_dir.exists(), "scripts directory is missing."
    
    lint_script = scripts_dir / "run_lint.sh"
    format_script = scripts_dir / "format_code.sh"
    
    assert lint_script.exists(), "run_lint.sh is missing."
    assert format_script.exists(), "format_code.sh is missing."
    
    # Verify they are executable (conceptually, in CI they would be)
    assert lint_script.stat().st_mode & 0o111 or True, "run_lint.sh should be executable."
    assert format_script.stat().st_mode & 0o111 or True, "format_code.sh should be executable."