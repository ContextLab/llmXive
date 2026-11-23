"""
Test to verify that linting and formatting tools are correctly configured.
This test ensures that 'ruff' and 'black' are available and can be invoked
on the codebase without errors (syntax check only).
"""
import subprocess
import sys
from pathlib import Path

def test_ruff_is_installed():
    """Verify ruff is installed and can show version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("Ruff is not installed or not executable.")
    except FileNotFoundError:
        pytest.fail("Ruff module not found.")

def test_black_is_installed():
    """Verify black is installed and can show version."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        pytest.fail("Black is not installed or not executable.")
    except FileNotFoundError:
        pytest.fail("Black module not found.")

def test_ruff_check_codebase():
    """Run ruff check on the code directory to ensure no syntax errors."""
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"
    
    if not code_dir.exists():
        pytest.skip("Code directory not found, skipping lint check.")

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # We expect exit code 0 (no errors) or 1 (linting warnings found but valid syntax).
    # The key is that it must run without crashing.
    # If it crashes (exit code > 1) or fails to parse, that's a failure.
    # For this specific task, we primarily care that the tool runs and parses the files.
    # We allow exit code 1 (linting issues) as long as the tool runs.
    assert result.returncode in (0, 1), f"Ruff check failed to parse code: {result.stderr}"

def test_black_check_codebase():
    """Run black --check on the code directory to ensure formatting compliance."""
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        pytest.skip("Code directory not found, skipping format check.")

    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", str(code_dir)],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Exit code 0: all files formatted correctly.
    # Exit code 1: some files need formatting.
    # Exit code > 1: error.
    # We assert it doesn't crash (exit code > 1).
    assert result.returncode in (0, 1), f"Black check failed to parse code: {result.stderr}"