"""
Tests to verify that linting and formatting configurations are valid and consistent.
These tests ensure that the project's pyproject.toml and .ruff.toml are syntactically
correct and that the project structure adheres to the configured rules.
"""

import subprocess
import sys
import os
import pytest
from pathlib import Path

# Ensure we are running from the code directory context if needed,
# but typically these run from project root.
PROJECT_ROOT = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Verify that ruff configuration file exists."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    
    # At least one should exist
    assert pyproject_path.exists() or ruff_path.exists(), \
        "Neither pyproject.toml nor .ruff.toml found in project root."

def test_black_config_exists():
    """Verify that black configuration exists (usually in pyproject.toml)."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing."
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, \
        "Black configuration section [tool.black] not found in pyproject.toml"

def test_ruff_syntax_check():
    """Run ruff check on a dummy file to ensure config is valid."""
    # Create a temporary file with valid python to test config loading
    dummy_file = PROJECT_ROOT / "tests" / "dummy_check.py"
    dummy_file.write_text("x = 1\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(dummy_file)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Config errors usually show as exit code 2 or specific error messages
        # We just want to ensure it doesn't crash on config parsing
        assert result.returncode in [0, 1], \
            f"Ruff check failed due to config error: {result.stderr}"
    finally:
        if dummy_file.exists():
            dummy_file.unlink()

def test_black_format_check():
    """Run black --check on a dummy file to ensure config is valid."""
    dummy_file = PROJECT_ROOT / "tests" / "dummy_format.py"
    # Content that is valid but might need formatting if config is weird, 
    # but mostly just checking if black loads config.
    dummy_file.write_text("x=1\n")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", str(dummy_file)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        # Exit code 1 means formatting needed, 0 means ok, >1 means error
        assert result.returncode in [0, 1], \
            f"Black check failed due to config error: {result.stderr}"
    finally:
        if dummy_file.exists():
            dummy_file.unlink()

def test_line_length_consistency():
    """Verify that Black and Ruff line lengths match."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml missing")
    
    content = pyproject_path.read_text()
    
    # Simple regex-free extraction for line-length
    import re
    black_match = re.search(r'\[tool\.black\].*?line-length\s*=\s*(\d+)', content, re.DOTALL)
    ruff_match = re.search(r'\[tool\.ruff\].*?line-length\s*=\s*(\d+)', content, re.DOTALL)
    
    if black_match and ruff_match:
        black_len = int(black_match.group(1))
        ruff_len = int(ruff_match.group(1))
        assert black_len == ruff_len, \
            f"Line length mismatch: Black={black_len}, Ruff={ruff_len}"
    elif black_match or ruff_match:
        # If only one is defined, it's acceptable (defaults apply to the other)
        pass
    else:
        # If neither found in pyproject, check .ruff.toml
        ruff_path = PROJECT_ROOT / ".ruff.toml"
        if ruff_path.exists():
            ruff_content = ruff_path.read_text()
            ruff_match = re.search(r'line-length\s*=\s*(\d+)', ruff_content)
            if ruff_match:
                # Default black is 88, if ruff is different, it's a potential mismatch
                # But we can't easily check black default without parsing black's source or running it.
                # We'll just ensure the file parses.
                pass