"""
Tests to verify that linting and formatting configurations are valid.

These tests ensure that:
1. The pyproject.toml file exists and is valid TOML.
2. The .ruff.toml file exists and is valid TOML.
3. The .gitignore file exists and contains expected patterns.
4. The requirements.txt file includes ruff and black.
"""
import os
import sys
from pathlib import Path
import tomllib

# Add code directory to path for imports if needed, though these tests are file-based
CODE_DIR = Path(__file__).parent.parent / "code"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in the code directory."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

def test_pyproject_toml_valid():
    """Verify pyproject.toml is valid TOML and contains black settings."""
    pyproject_path = CODE_DIR / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise AssertionError(f"pyproject.toml is not valid TOML: {e}")
    
    assert "tool" in data, "Missing 'tool' section in pyproject.toml"
    assert "black" in data["tool"], "Missing [tool.black] section"
    assert "ruff" in data["tool"], "Missing [tool.ruff] section"
    assert data["tool"]["black"]["line-length"] == 88, "Black line-length should be 88"

def test_ruff_toml_exists():
    """Verify .ruff.toml exists in the code directory."""
    ruff_path = CODE_DIR / ".ruff.toml"
    assert ruff_path.exists(), f".ruff.toml not found at {ruff_path}"

def test_ruff_toml_valid():
    """Verify .ruff.toml is valid TOML and contains expected lint rules."""
    ruff_path = CODE_DIR / ".ruff.toml"
    with open(ruff_path, "rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise AssertionError(f".ruff.toml is not valid TOML: {e}")
    
    assert "lint" in data, "Missing [lint] section in .ruff.toml"
    assert "select" in data["lint"], "Missing 'select' in [lint]"
    # Check for standard error codes
    assert "E" in data["lint"]["select"], "Should include pycodestyle errors (E)"
    assert "F" in data["lint"]["select"], "Should include Pyflakes (F)"

def test_gitignore_exists():
    """Verify .gitignore exists in the code directory."""
    gitignore_path = CODE_DIR / ".gitignore"
    assert gitignore_path.exists(), f".gitignore not found at {gitignore_path}"

def test_gitignore_contains_large_file_rules():
    """Verify .gitignore contains rules for large data files."""
    gitignore_path = CODE_DIR / ".gitignore"
    content = gitignore_path.read_text()
    
    # Check for expected patterns
    assert "data/raw/*.nii" in content, "Missing rule for ignoring NIfTI files"
    assert "outputs/*.pdf" in content, "Missing rule for ignoring PDF outputs"
    assert "logs/*.log" in content, "Missing rule for ignoring log files"
    assert ".env" in content, "Missing rule for ignoring .env files"

def test_requirements_includes_linting_tools():
    """Verify requirements.txt includes ruff and black."""
    req_path = CODE_DIR / "requirements.txt"
    assert req_path.exists(), f"requirements.txt not found at {req_path}"
    
    content = req_path.read_text().lower()
    assert "ruff" in content, "requirements.txt should include 'ruff'"
    assert "black" in content, "requirements.txt should include 'black'"