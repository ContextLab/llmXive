import os
import subprocess
from pathlib import Path

def test_ruff_toml_exists():
    """Verify ruff.toml exists and contains required settings."""
    assert Path("ruff.toml").exists(), "ruff.toml not found"
    content = Path("ruff.toml").read_text()
    assert "line-length = 88" in content, "Missing line-length in ruff.toml"
    assert 'target-version = "py39"' in content, "Missing target-version in ruff.toml"
    assert 'select = ["E", "F", "W", "I"]' in content, "Missing select in ruff.toml"

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists and contains black settings."""
    assert Path("pyproject.toml").exists(), "pyproject.toml not found"
    content = Path("pyproject.toml").read_text()
    assert "[tool.black]" in content, "Missing [tool.black] section"
    assert "line-length = 88" in content, "Missing line-length in pyproject.toml"
    assert "py39" in content, "Missing py39 target in pyproject.toml"

def test_ruff_available():
    """Verify ruff is installed in the environment."""
    result = subprocess.run(["ruff", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, f"ruff not available: {result.stderr}"

def test_black_available():
    """Verify black is installed in the environment."""
    result = subprocess.run(["black", "--version"], capture_output=True, text=True)
    assert result.returncode == 0, f"black not available: {result.stderr}"