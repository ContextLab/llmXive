"""Contract test for linting and formatting configuration.

Verifies that ruff and black configuration files exist and that
running the tools on the codebase returns zero exit codes.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"

def test_ruff_config_exists():
    """Verify ruff.toml exists."""
    ruff_config = CODE_DIR / "ruff.toml"
    assert ruff_config.exists(), f"ruff.toml missing at {ruff_config}"

def test_black_config_exists():
    """Verify pyproject.toml contains black configuration."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml missing"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "Black configuration not found in pyproject.toml"

def test_ruff_check_passes():
    """Run `ruff check .` and assert it returns 0."""
    # Ensure ruff is installed
    try:
        import ruff  # noqa: F401
    except ImportError:
        pytest.skip("ruff not installed")

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(PROJECT_ROOT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"ruff check failed with code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )

def test_black_check_passes():
    """Run `black --check .` and assert it returns 0."""
    # Ensure black is installed
    try:
        import black  # noqa: F401
    except ImportError:
        pytest.skip("black not installed")

    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(PROJECT_ROOT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"black --check failed with code {result.returncode}\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )