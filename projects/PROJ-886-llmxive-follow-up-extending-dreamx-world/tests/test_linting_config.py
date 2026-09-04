"""
Test suite to verify that linting and formatting configurations are valid.
This ensures ruff and black are correctly configured before running on code.
"""
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
RUFF_CONFIG = PROJECT_ROOT / "pyproject.toml"
BLACK_CONFIG = PROJECT_ROOT / "pyproject.toml"


def test_ruff_check_syntax():
    """Run ruff check on the project to ensure configuration is valid."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--output-format=concise", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # We expect some errors in a new project, but the command must run without config errors.
        # If the config is invalid, ruff exits with code 2.
        assert result.returncode != 2, f"Ruff configuration error:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Ruff check timed out")
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")


def test_black_check_format():
    """Run black --check on the project to ensure configuration is valid."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # Black returns 0 if all good, 1 if needs reformatting, 2 if config error.
        # We only care that it doesn't crash due to config (code 2).
        assert result.returncode != 2, f"Black configuration error:\n{result.stderr}"
    except subprocess.TimeoutExpired:
        pytest.fail("Black check timed out")
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")


def test_pyproject_toml_exists():
    """Verify pyproject.toml exists in the project root."""
    assert RUFF_CONFIG.exists(), "pyproject.toml not found"
    content = RUFF_CONFIG.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"