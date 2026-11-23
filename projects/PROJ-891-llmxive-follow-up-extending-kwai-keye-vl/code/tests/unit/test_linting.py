import pytest
from pathlib import Path
import os
import sys
import subprocess

def test_ruff_config_exists():
    """Verify .ruff.toml or pyproject.toml with ruff config exists."""
    project_root = Path(__file__).parent.parent.parent
    ruff_toml = project_root / ".ruff.toml"
    pyproject = project_root / "pyproject.toml"
    
    assert ruff_toml.exists() or pyproject.exists(), "Ruff configuration file not found"

def test_black_config_exists():
    """Verify pyproject.toml with black config exists."""
    project_root = Path(__file__).parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    
    assert pyproject.exists(), "pyproject.toml not found"
    
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"

def test_requirements_contains_linting_tools():
    """Verify dev dependencies include ruff and black."""
    project_root = Path(__file__).parent.parent.parent
    pyproject = project_root / "pyproject.toml"
    
    content = pyproject.read_text()
    assert "ruff" in content, "Ruff not found in dependencies"
    assert "black" in content, "Black not found in dependencies"

def test_ruff_can_run():
    """Verify ruff is installed and can run."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Ruff failed to run: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("Ruff is not installed")

def test_black_can_run():
    """Verify black is installed and can run."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"Black failed to run: {result.stderr}"
    except FileNotFoundError:
        pytest.fail("Black is not installed")

def test_setup_linting_script_exists():
    """Verify the setup script for linting exists."""
    project_root = Path(__file__).parent.parent.parent
    setup_script = project_root / "scripts" / "setup_linting.sh"
    
    assert setup_script.exists(), "setup_linting.sh not found"