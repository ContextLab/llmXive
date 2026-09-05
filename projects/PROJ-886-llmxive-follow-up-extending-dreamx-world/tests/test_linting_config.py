"""
Integration test to verify linting and formatting configurations are correct.
This test ensures that `ruff check` and `black --check` pass without errors.
"""
import subprocess
import sys
import os
import tempfile
from pathlib import Path

def test_ruff_check_passes():
    """Verify that ruff check passes on the codebase."""
    # Run ruff check on the current directory
    result = subprocess.run(
        ["ruff", "check", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    # If ruff is not installed, skip (in CI it should be installed)
    if result.returncode == 127:
        print("Ruff not found, skipping test")
        return
    
    # Assert no errors (returncode 0)
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes():
    """Verify that black --check passes on the codebase."""
    # Run black check on the current directory
    result = subprocess.run(
        ["black", "--check", "."],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent
    )
    
    # If black is not installed, skip
    if result.returncode == 127:
        print("Black not found, skipping test")
        return
    
    # Assert no formatting issues (returncode 0)
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_config_files_exist():
    """Verify that required config files exist."""
    base_dir = Path(__file__).parent.parent
    assert (base_dir / "pyproject.toml").exists(), "pyproject.toml missing"
    assert (base_dir / ".ruff.toml").exists(), ".ruff.toml missing"
    
    # Verify content contains expected sections
    pyproject_content = (base_dir / "pyproject.toml").read_text()
    assert "[tool.black]" in pyproject_content, "Missing [tool.black] section"
    assert "[tool.ruff]" in pyproject_content, "Missing [tool.ruff] section"

    ruff_content = (base_dir / ".ruff.toml").read_text()
    assert "target-version" in ruff_content, "Missing target-version in .ruff.toml"
    assert "line-length" in ruff_content, "Missing line-length in .ruff.toml"