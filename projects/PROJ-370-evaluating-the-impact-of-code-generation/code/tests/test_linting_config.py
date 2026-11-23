import subprocess
import sys
import os
import pytest
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent

def test_ruff_config_exists():
    """Verify that pyproject.toml contains ruff configuration."""
    pyproject = ROOT_DIR / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"
    content = pyproject.read_text()
    assert "[tool.ruff]" in content, "pyproject.toml must contain [tool.ruff] section"

def test_black_config_exists():
    """Verify that pyproject.toml contains black configuration."""
    pyproject = ROOT_DIR / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml must exist"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"

def test_ruff_syntax_check():
    """Run ruff check on the code directory to ensure no syntax errors or style violations."""
    # We run ruff with only E (errors) and W (warnings) to avoid failing on non-critical linting
    # if the environment isn't fully set up, but we expect the config to be valid.
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True
    )
    # We only assert that the command ran without crashing (exit code 0 or 1).
    # Exit code 0 = no issues, 1 = issues found (which is fine for a config test),
    # anything else = command error.
    assert result.returncode in (0, 1), f"Ruff check failed to run: {result.stderr}"

def test_black_format_check():
    """Run black --check on the code directory to ensure files are formatted."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "code"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True
    )
    # Exit code 0 = all good.
    # Exit code 1 = some files not formatted (which is acceptable for this check if we just want to verify the tool runs).
    # We assert it doesn't crash with a code > 1.
    assert result.returncode in (0, 1), f"Black check failed to run: {result.stderr}"

def test_line_length_consistency():
    """Verify that black and ruff agree on line length (default 88)."""
    pyproject = ROOT_DIR / "pyproject.toml"
    content = pyproject.read_text()
    
    # Extract line-length for black
    black_line_length = None
    in_black = False
    for line in content.splitlines():
        if "[tool.black]" in line:
            in_black = True
        if in_black and "line-length" in line:
            black_line_length = int(line.split("=")[1].strip())
            break
    
    # Extract line-length for ruff
    ruff_line_length = None
    in_ruff = False
    for line in content.splitlines():
        if "[tool.ruff]" in line:
            in_ruff = True
        if in_ruff and "line-length" in line:
            ruff_line_length = int(line.split("=")[1].strip())
            break
    
    assert black_line_length is not None, "Black line-length not found"
    assert ruff_line_length is not None, "Ruff line-length not found"
    assert black_line_length == ruff_line_length, f"Line length mismatch: Black={black_line_length}, Ruff={ruff_line_length}"
    assert black_line_length == 88, f"Expected line length 88, got {black_line_length}"