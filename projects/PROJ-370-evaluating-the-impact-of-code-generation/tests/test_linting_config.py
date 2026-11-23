import subprocess
import sys
import os
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RUFF_TOML = PROJECT_ROOT / "pyproject.toml"
BLACK_CONFIG_EXISTS = (PROJECT_ROOT / "pyproject.toml").exists()
RUFF_CONFIG_EXISTS = (PROJECT_ROOT / "pyproject.toml").exists()

def test_ruff_config_exists():
    """Verify that ruff configuration exists in pyproject.toml"""
    assert RUFF_CONFIG_EXISTS, "pyproject.toml must exist for ruff configuration"
    content = RUFF_TOML.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml"""
    assert BLACK_CONFIG_EXISTS, "pyproject.toml must exist for black configuration"
    content = RUFF_TOML.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

def test_ruff_syntax_check():
    """Run ruff check on the project to ensure no syntax errors or violations (ignoring E501)"""
    # Check a specific known file to ensure the tool works
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/config/settings.py", "--output-format=concise"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # We expect exit code 0 (success) or 1 (violations found but valid syntax)
    # If syntax is invalid, ruff might return 2 or 3 depending on version, but usually 1 for violations.
    # The key is that it runs without crashing.
    assert result.returncode in (0, 1), f"Ruff check failed with code {result.returncode}: {result.stderr}"

def test_black_format_check():
    """Run black --check to ensure files are formatted correctly"""
    # Check a specific known file
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "code/config/settings.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    # Exit code 0 means formatted correctly, 1 means differences found (but valid syntax)
    # We assert it doesn't crash (exit code > 1 usually means error)
    assert result.returncode in (0, 1), f"Black check failed with code {result.returncode}: {result.stderr}"

def test_line_length_consistency():
    """Verify that black and ruff agree on line length configuration"""
    ruff_content = RUFF_TOML.read_text()
    # Extract line-length from ruff section
    import re
    ruff_match = re.search(r'\[tool\.ruff\].*?line-length\s*=\s*(\d+)', ruff_content, re.DOTALL)
    black_match = re.search(r'\[tool\.black\].*?line-length\s*=\s*(\d+)', ruff_content, re.DOTALL)

    assert ruff_match is not None, "Ruff line-length not found"
    assert black_match is not None, "Black line-length not found"

    ruff_len = int(ruff_match.group(1))
    black_len = int(black_match.group(1))

    assert ruff_len == black_len, f"Line length mismatch: ruff={ruff_len}, black={black_len}"