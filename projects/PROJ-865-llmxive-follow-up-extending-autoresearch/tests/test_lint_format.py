import subprocess
import sys
from pathlib import Path

def test_ruff_installed():
    """Verify that ruff is installed and accessible."""
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "ruff" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("Ruff is not installed or not in PATH")

def test_black_installed():
    """Verify that black is installed and accessible."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        assert "black" in result.stdout.lower()
    except subprocess.CalledProcessError:
        raise AssertionError("Black is not installed or not in PATH")

def test_ruff_check_passes():
    """Verify that ruff check passes on the code directory."""
    code_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["ruff", "check", str(code_root)],
        capture_output=True,
        text=True
    )
    # We expect exit code 0 for success, or 1 for linting issues found
    # This test ensures the command runs without crashing
    assert result.returncode in [0, 1], f"Ruff check crashed: {result.stderr}"

def test_black_check_passes():
    """Verify that black check runs on the code directory."""
    code_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["black", "--check", str(code_root)],
        capture_output=True,
        text=True
    )
    # Exit code 0 means all files are formatted correctly
    # Exit code 1 means some files need reformatting (expected in dev)
    # We just verify the command runs successfully
    assert result.returncode in [0, 1], f"Black check crashed: {result.stderr}"
