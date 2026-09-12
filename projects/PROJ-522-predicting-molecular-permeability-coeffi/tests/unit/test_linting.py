"""Unit tests for linting configuration."""
import os
import subprocess
import sys
from pathlib import Path

def test_ruff_config_exists():
    """Test that ruff.toml exists and is valid."""
    ruff_path = Path("code/ruff.toml")
    assert ruff_path.exists(), "ruff.toml should exist"
    
    # Try to parse it with ruff
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(ruff_path), "code/"],
        capture_output=True,
        text=True
    )
    # Should not crash, even if there are linting errors
    assert result.returncode in [0, 1], "Ruff should run without crashing"

def test_black_config_exists():
    """Test that pypyproject.toml exists and is valid."""
    black_path = Path("pypyproject.toml")
    assert black_path.exists(), "pypyproject.toml should exist"
    
    # Try to run black with config
    result = subprocess.run(
        [sys.executable, "-m", "black", "--config", str(black_path), "--check", "code/"],
        capture_output=True,
        text=True
    )
    # Should not crash, even if there are formatting issues
    assert result.returncode in [0, 1], "Black should run without crashing"

def test_setup_linting_script_exists():
    """Test that setup_linting.py exists."""
    script_path = Path("code/setup_linting.py")
    assert script_path.exists(), "setup_linting.py should exist"

def test_linting_tools_installable():
    """Test that linting tools can be imported."""
    try:
        import ruff
        import black
        assert True, "Linting tools are installed"
    except ImportError as e:
        assert False, f"Linting tools not installed: {e}"