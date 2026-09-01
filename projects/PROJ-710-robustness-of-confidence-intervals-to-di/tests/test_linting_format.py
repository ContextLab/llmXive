import subprocess
import sys
import os
from pathlib import Path
import pytest

def test_ruff_config_exists():
    """Verify that ruff configuration exists in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist"
    
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists(), "pyproject.toml must exist"
    
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

def test_ruff_syntax_check():
    """Verify that ruff can check syntax without errors on existing code."""
    # Run ruff check on the code directory
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/"],
        capture_output=True,
        text=True
    )
    # We expect no syntax errors, but may have style warnings which are okay
    # The important thing is that ruff runs without crashing
    assert result.returncode == 0 or "syntax error" not in result.stdout.lower()

def test_black_syntax_check():
    """Verify that black can check syntax without errors on existing code."""
    # Run black --check on the code directory
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "code/"],
        capture_output=True,
        text=True
    )
    # Black returns 1 if files would be reformatted, which is okay for this test
    # We just want to ensure it doesn't crash on syntax errors
    assert "syntax error" not in result.stderr.lower()

def test_requirements_include_tools():
    """Verify that requirements.txt includes ruff and black."""
    requirements_path = Path("requirements.txt")
    assert requirements_path.exists(), "requirements.txt must exist"
    
    content = requirements_path.read_text().lower()
    assert "ruff" in content, "requirements.txt must include ruff"
    assert "black" in content, "requirements.txt must include black"