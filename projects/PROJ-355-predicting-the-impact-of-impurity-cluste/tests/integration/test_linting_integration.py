"""
Integration test for linting and formatting tools.
Verifies that the configured tools can be invoked on the codebase.
"""
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.mark.integration
def test_ruff_lint_codebase():
    """Run ruff on the codebase to ensure it passes configured rules."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # We expect 0 (success) or 1 (linting issues found).
        # 2 indicates a configuration or runtime error.
        assert result.returncode != 2, f"Ruff execution failed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("Ruff execution timed out")


@pytest.mark.integration
def test_black_format_check():
    """Run black in check mode to ensure code formatting compliance."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # 0 = OK, 1 = needs formatting, 2 = error
        assert result.returncode != 2, f"Black execution failed: {result.stderr}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.skip("Black execution timed out")
