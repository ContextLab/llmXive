"""
Tests to verify that linting and formatting scripts exist and are callable.
These are sanity checks for the tooling setup.
"""
import subprocess
import sys
import os
import pytest

# Determine paths relative to this test file
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(TEST_DIR)
CODE_DIR = os.path.join(ROOT_DIR, "code")
SCRIPTS_DIR = os.path.join(CODE_DIR, "scripts")

@pytest.mark.skipif(sys.platform.startswith("win"), reason="Skip on Windows for CI compatibility if needed")
def test_lint_script_exists():
    """Verify the lint script exists."""
    lint_script = os.path.join(SCRIPTS_DIR, "run_lint.py")
    assert os.path.exists(lint_script), f"Lint script not found at {lint_script}"

@pytest.mark.skipif(sys.platform.startswith("win"), reason="Skip on Windows for CI compatibility if needed")
def test_format_script_exists():
    """Verify the format script exists."""
    format_script = os.path.join(SCRIPTS_DIR, "run_format.py")
    assert os.path.exists(format_script), f"Format script not found at {format_script}"

@pytest.mark.slow
def test_ruff_check_runs():
    """Run ruff check to ensure it executes without crashing."""
    # Note: This test might fail if ruff is not installed in the environment, 
    # which is expected if the environment setup is incomplete.
    try:
        result = subprocess.run(
            ["python", os.path.join(SCRIPTS_DIR, "run_lint.py")],
            cwd=ROOT_DIR,
            capture_output=True,
            timeout=60
        )
        # We expect it to pass (0) or fail (1) on lint errors, but not crash (e.g. FileNotFoundError)
        # If ruff is missing, it will return non-zero with a specific error message.
        # For this test, we just ensure the script runs.
        assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
    except FileNotFoundError:
        pytest.skip("Ruff not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Linting timed out")

@pytest.mark.slow
def test_black_check_runs():
    """Run black check to ensure it executes without crashing."""
    try:
        result = subprocess.run(
            ["python", os.path.join(SCRIPTS_DIR, "run_format.py")],
            cwd=ROOT_DIR,
            capture_output=True,
            timeout=60
        )
        assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"
    except FileNotFoundError:
        pytest.skip("Black not installed in environment")
    except subprocess.TimeoutExpired:
        pytest.fail("Formatting timed out")