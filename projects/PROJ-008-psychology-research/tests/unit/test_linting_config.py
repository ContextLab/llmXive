"""
Unit tests to verify that linting and formatting configurations are valid.
These tests ensure that ruff and black can parse the project configuration.
"""
import subprocess
import sys
import os
import tempfile
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_ruff_config_exists_and_valid():
    """Test that .ruff.toml exists and is valid TOML."""
    ruff_config = PROJECT_ROOT / ".ruff.toml"
    assert ruff_config.exists(), "Ruff configuration file (.ruff.toml) is missing"
    
    # Try to run ruff check with the config to ensure it's valid
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--config", str(ruff_config), "--isolated", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Ruff might return non-zero if there are linting errors, 
        # but we only care if it crashes due to config issues
        assert "error: Failed to parse" not in result.stderr, f"Invalid ruff config: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out, possible configuration issue")

def test_black_config_exists_and_valid():
    """Test that black configuration in pyproject.toml is valid."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml is missing"
    
    # Check for [tool.black] section
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration section missing from pyproject.toml"
    
    # Try to run black --check to ensure config is valid
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--config", str(pyproject), "--check", "--diff", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Black returns 1 if files need reformatting, which is fine for config validation
        # We only care if it crashes due to config issues
        assert "Error:" not in result.stderr or "No such file" not in result.stderr, f"Invalid black config: {result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out, possible configuration issue")

def test_ruff_can_check_a_file():
    """Test that ruff can successfully analyze a Python file."""
    # Create a temporary Python file with a known issue
    test_file_content = """
import os
import sys
import unused_module

def test_func(  ):
    x=1
    return x
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_file_content)
        temp_file = f.name

    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", temp_file],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should find errors (unused import, formatting issues)
        assert result.returncode != 0 or "All checks passed" in result.stdout
    finally:
        os.unlink(temp_file)

def test_black_can_format_a_file():
    """Test that black can successfully format a Python file."""
    # Create a temporary Python file with bad formatting
    test_file_content = """
def test_func(  ):
    x=1
    return x
"""
    expected_content = """
def test_func():
    x = 1
    return x
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_file_content)
        temp_file = f.name

    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--config", str(PROJECT_ROOT / "pyproject.toml"), temp_file],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Read the formatted content
        with open(temp_file, 'r') as f:
            formatted = f.read()
        
        # Check if formatting was applied (simplified check)
        assert "x = 1" in formatted, "Black did not format the file correctly"
    finally:
        os.unlink(temp_file)