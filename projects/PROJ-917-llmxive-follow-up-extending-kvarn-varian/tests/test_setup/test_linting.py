"""
Tests for T003: Configure linting (ruff) and formatting (black) tools.
"""
import pytest
import subprocess
import sys
from pathlib import Path

def check_tool_installed(tool_name: str) -> bool:
    """Check if a tool is installed and accessible."""
    try:
        subprocess.run(
            [sys.executable, "-m", tool_name, "--version"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def test_ruff_is_installed():
    """Test that ruff is installed."""
    assert check_tool_installed("ruff"), "ruff must be installed"

def test_black_is_installed():
    """Test that black is installed."""
    assert check_tool_installed("black"), "black must be installed"

def test_ruff_config_exists():
    """Test that ruff.toml configuration file exists."""
    project_root = Path(__file__).resolve().parent.parent.parent
    ruff_config = project_root / "ruff.toml"
    assert ruff_config.exists(), "ruff.toml configuration file must exist"

def test_black_config_in_pyproject():
    """Test that black configuration exists in pyproject.toml."""
    project_root = Path(__file__).resolve().parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"
    
    with open(pyproject, "r") as f:
        content = f.read()
    
    assert "[tool.black]" in content, "black configuration must be in pyproject.toml"

def test_ruff_can_check_code():
    """Test that ruff can run on the codebase."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    # Ruff should run without crashing (exit code 0 or 1 is fine, 2 is error)
    assert result.returncode != 2, f"ruff check failed: {result.stderr}"

def test_black_can_format_code():
    """Test that black can run on the codebase."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
        capture_output=True,
        text=True,
    )
    # Black should run without crashing (exit code 0 or 1 is fine, 2 is error)
    assert result.returncode != 2, f"black check failed: {result.stderr}"
