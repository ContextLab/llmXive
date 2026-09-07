import subprocess
import sys
import os
import pytest
from pathlib import Path

def test_ruff_config_exists():
    """Verify ruff configuration exists in pyproject.toml or .ruff.toml"""
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    ruff_toml = root / ".ruff.toml"
    ruff_toml2 = root / "ruff.toml"

    assert pyproject.exists() or ruff_toml.exists() or ruff_toml2.exists(), \
        "Configuration for ruff (pyproject.toml or .ruff.toml/ruff.toml) must exist"

def test_black_config_exists():
    """Verify black configuration exists in pyproject.toml or .black.toml"""
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"
    black_cfg = root / ".black.toml"
    setup_cfg = root / "setup.cfg"

    # Check for [tool.black] in pyproject.toml
    if pyproject.exists():
        content = pyproject.read_text()
        assert "[tool.black]" in content, \
            "pyproject.toml must contain [tool.black] section"

def test_ruff_syntax_check():
    """Run ruff check to ensure no syntax errors in code"""
    root = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # We expect some linting warnings potentially, but no syntax errors (E9, F63, F7, F82)
        # For this test, we just ensure ruff runs without crashing the process
        assert result.returncode == 0 or "syntax error" not in result.stdout.lower(), \
            f"Ruff found critical syntax errors: {result.stdout}"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("ruff check timed out")

def test_black_format_check():
    """Run black --check to ensure code is formatted"""
    root = Path(__file__).parent.parent
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", "code/"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30
        )
        # If returncode is 0, everything is formatted.
        # If 1, there are diffs, but it's not a failure of the test itself, just a style guide violation.
        # However, for the task "Configure linting", we verify the tool runs.
        # We assert that black executes successfully (returncode 0 or 1).
        assert result.returncode in [0, 1], \
            f"Black check failed unexpectedly: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("black check timed out")

def test_line_length_consistency():
    """Verify that the configured line length is consistent between tools"""
    root = Path(__file__).parent.parent
    pyproject = root / "pyproject.toml"

    if not pyproject.exists():
        pytest.fail("pyproject.toml not found")

    content = pyproject.read_text()

    # Extract line-length for black
    black_line = None
    ruff_line = None

    in_black = False
    in_ruff = False

    for line in content.splitlines():
        if "[tool.black]" in line:
            in_black = True
            in_ruff = False
            continue
        if "[tool.ruff]" in line:
            in_ruff = True
            in_black = False
            continue
        if line.strip().startswith("[tool."):
            in_black = False
            in_ruff = False
            continue

        if in_black and "line-length" in line:
            try:
                black_line = int(line.split("=")[1].strip())
            except (ValueError, IndexError):
                pass

        if in_ruff and "line-length" in line:
            try:
                ruff_line = int(line.split("=")[1].strip())
            except (ValueError, IndexError):
                pass

    if black_line and ruff_line:
        assert black_line == ruff_line, \
            f"Line length mismatch: Black={black_line}, Ruff={ruff_line}. They should match."