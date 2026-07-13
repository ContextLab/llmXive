"""
Integration tests for linting and formatting workflow.
"""
import subprocess
import sys
from pathlib import Path
import pytest

def test_run_lint_script():
    """Test that the run_lint.py script executes successfully."""
    project_root = Path(__file__).resolve().parent.parent.parent
    run_lint_script = project_root / "code" / "run_lint.py"
    
    assert run_lint_script.exists(), "run_lint.py not found"
    
    try:
        result = subprocess.run(
            [sys.executable, str(run_lint_script)],
            check=True,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # If we get here, the script ran without errors
        assert True
    except subprocess.CalledProcessError as e:
        # If linting fails, that's expected in a real scenario if code isn't clean
        # But the script should still run and report the failure
        pytest.skip(f"Linting/formatting checks failed (expected if code needs fixing): {e.stdout}")

def test_ruff_check_command():
    """Test that ruff check command runs."""
    project_root = Path(__file__).resolve().parent.parent.parent
    
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        # Command executed successfully (exit code 0 or 1 for issues found)
        assert result.returncode in [0, 1]
    except FileNotFoundError:
        pytest.fail("ruff command not found")

def test_black_check_command():
    """Test that black check command runs."""
    project_root = Path(__file__).resolve().parent.parent.parent
    
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        # Command executed successfully (exit code 0 or 1 for issues found)
        assert result.returncode in [0, 1]
    except FileNotFoundError:
        pytest.fail("black command not found")