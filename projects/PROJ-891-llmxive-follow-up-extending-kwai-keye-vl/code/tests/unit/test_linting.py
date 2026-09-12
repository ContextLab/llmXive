import pytest
from pathlib import Path
import os
import sys
import subprocess

def test_ruff_config_exists():
    """Test that .ruff.toml configuration file exists."""
    assert Path(".ruff.toml").exists(), "ruff configuration file (.ruff.toml) not found"

def test_black_config_exists():
    """Test that pyproject.toml contains Black configuration."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml not found"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration section not found in pyproject.toml"

def test_requirements_contains_linting_tools():
    """Test that requirements.txt contains ruff and black."""
    req_path = Path("requirements.txt")
    assert req_path.exists(), "requirements.txt not found"
    
    content = req_path.read_text()
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"

def test_ruff_can_run():
    """Test that ruff command is available and can run."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"ruff command failed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("ruff command timed out")

def test_black_can_run():
    """Test that black command is available and can run."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0, f"black command failed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("black command timed out")

def test_setup_linting_script_exists():
    """Test that setup_linting.py script exists and has main function."""
    script_path = Path("code/setup_linting.py")
    assert script_path.exists(), "setup_linting.py script not found"
    
    # Verify it can be imported
    spec = __import__("importlib.util").util.spec_from_file_location("setup_linting", script_path)
    module = __import__("importlib.util").util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    assert hasattr(module, "main"), "setup_linting.py missing main function"
    assert hasattr(module, "write_ruff_config"), "setup_linting.py missing write_ruff_config function"
    assert hasattr(module, "write_black_config"), "setup_linting.py missing write_black_config function"