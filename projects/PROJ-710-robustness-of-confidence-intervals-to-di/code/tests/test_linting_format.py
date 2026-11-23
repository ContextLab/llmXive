import subprocess
import sys
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def test_ruff_config_exists():
    """Verify that a ruff configuration file exists in the project root."""
    ruff_config = PROJECT_ROOT / "pyproject.toml"
    assert ruff_config.exists(), f"pyproject.toml (ruff config) not found at {ruff_config}"
    content = ruff_config.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml missing [tool.ruff] section"

def test_black_config_exists():
    """Verify that a black configuration exists (usually in pyproject.toml)."""
    black_config = PROJECT_ROOT / "pyproject.toml"
    assert black_config.exists(), f"pyproject.toml (black config) not found at {black_config}"
    content = black_config.read_text()
    assert "[tool.black]" in content, "pyproject.toml missing [tool.black] section"

def test_ruff_syntax_check():
    """Run ruff check on the code directory to ensure no syntax/lint errors."""
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        pytest.skip("code directory not found, skipping lint check")
    
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Ruff returns 0 if no issues, 1 if issues found
    # We expect 0 for a clean run, but if there are warnings we might want to allow them.
    # For this test, we strictly check for syntax errors or blocking lint issues.
    # If the project is new, we might have some warnings, but we ensure the command runs.
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_syntax_check():
    """Run black --check on the code directory to ensure formatting compliance."""
    code_dir = PROJECT_ROOT / "code"
    if not code_dir.exists():
        pytest.skip("code directory not found, skipping format check")
    
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Black returns 0 if files are formatted correctly, 1 if not
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_requirements_include_tools():
    """Verify that requirements.txt includes ruff and black."""
    req_file = PROJECT_ROOT / "requirements.txt"
    assert req_file.exists(), "requirements.txt not found"
    content = req_file.read_text().lower()
    assert "ruff" in content, "ruff not found in requirements.txt"
    assert "black" in content, "black not found in requirements.txt"
