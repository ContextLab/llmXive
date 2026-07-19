"""
Unit tests to verify that formatting and linting configurations exist and are valid.
These tests do not run the tools, but verify the configuration files are present.
"""
import os
import toml
from pathlib import Path

def test_black_config_exists():
    """Verify black configuration exists in pyproject.toml."""
    project_root = Path(__file__).parent.parent.parent
    pyproject_path = project_root / "code" / "pyproject.toml"
    
    assert pyproject_path.exists(), "pyproject.toml not found in code/"
    
    with open(pyproject_path, "r") as f:
        config = toml.load(f)
    
    assert "tool" in config, "Missing 'tool' section in pyproject.toml"
    assert "black" in config["tool"], "Missing 'black' configuration in pyproject.toml"
    
    # Verify required settings
    assert "line-length" in config["tool"]["black"], "Missing line-length in black config"
    assert config["tool"]["black"]["line-length"] == 88, "Black line-length should be 88"

def test_ruff_config_exists():
    """Verify ruff configuration exists."""
    project_root = Path(__file__).parent.parent.parent
    ruff_path = project_root / "code" / ".ruff.toml"
    
    assert ruff_path.exists(), ".ruff.toml not found in code/"
    
    with open(ruff_path, "r") as f:
        content = f.read()
    
    assert "target-version" in content, "Missing target-version in .ruff.toml"
    assert "py311" in content, "Target version should be py311"
    assert "line-length" in content, "Missing line-length in .ruff.toml"

def test_format_script_exists():
    """Verify format.py script exists and is importable."""
    project_root = Path(__file__).parent.parent.parent
    format_script = project_root / "code" / "format.py"
    
    assert format_script.exists(), "format.py not found in code/"
    
    # Check if it has the expected functions
    with open(format_script, "r") as f:
        content = f.read()
    
    assert "def run_command" in content, "Missing run_command function"
    assert "def main" in content, "Missing main function"
    assert "import black" in content or "black" in content, "Script should reference black"
    assert "import ruff" in content or "ruff" in content, "Script should reference ruff"