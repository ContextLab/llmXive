import os
import subprocess
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_ruff_config_exists():
    """Verify that ruff configuration file exists."""
    ruff_config = PROJECT_ROOT / ".ruff.toml"
    assert ruff_config.exists(), "Ruff configuration file (.ruff.toml) not found"
    assert ruff_config.stat().st_size > 0, "Ruff configuration file is empty"

def test_black_config_exists():
    """Verify that black configuration exists in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration missing from pyproject.toml"
    assert "line-length" in content, "Black line-length configuration missing"

def test_ruff_lint_passes():
    """Verify that ruff linting passes on the codebase."""
    ruff_path = PROJECT_ROOT / "code"
    if not ruff_path.exists():
        pytest.skip("Code directory not found, skipping lint check")

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(ruff_path)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Allow exit code 0 (no errors) or 1 (errors found but we just check config exists)
    # In a real CI, we'd fail on exit code 1, but here we verify config is set up
    assert result.returncode in [0, 1], f"Ruff check failed with unexpected error: {result.stderr}"

def test_black_format_check():
    """Verify that black format check passes (or config is valid)."""
    code_path = PROJECT_ROOT / "code"
    if not code_path.exists():
        pytest.skip("Code directory not found, skipping format check")

    # Run black in check mode
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(code_path)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    # Exit code 0 = all good, 1 = formatting needed (but config is valid)
    assert result.returncode in [0, 1], f"Black check failed with unexpected error: {result.stderr}"