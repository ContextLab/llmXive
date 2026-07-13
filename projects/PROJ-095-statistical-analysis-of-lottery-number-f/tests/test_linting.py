import subprocess
import sys
import os

def test_ruff_check():
    """Ensure ruff check passes on the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check():
    """Ensure black format check passes on the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code/", "tests/"],
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"