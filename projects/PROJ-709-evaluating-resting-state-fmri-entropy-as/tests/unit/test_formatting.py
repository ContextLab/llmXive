import subprocess
import sys
from pathlib import Path


def test_black_isort_installed():
    """Ensure black and isort are available in the environment."""
    result_black = subprocess.run(
        [sys.executable, "-m", "black", "--version"],
        capture_output=True,
        text=True,
    )
    result_isort = subprocess.run(
        [sys.executable, "-m", "isort", "--version"],
        capture_output=True,
        text=True,
    )
    assert result_black.returncode == 0, "black is not installed or not working"
    assert result_isort.returncode == 0, "isort is not installed or not working"


def test_code_is_formatted():
    """
    Verify that code/ and tests/ directories pass black and isort checks.
    This ensures T041a cleanup was successful.
    """
    repo_root = Path(__file__).parent.parent
    code_dir = repo_root / "code"
    tests_dir = repo_root / "tests"

    # Check isort
    result_isort = subprocess.run(
        [sys.executable, "-m", "isort", "--check-only", str(code_dir), str(tests_dir)],
        capture_output=True,
        text=True,
    )
    assert result_isort.returncode == 0, (
        f"isort check failed:\n{result_isort.stderr}\n{result_isort.stdout}"
    )

    # Check black
    result_black = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir), str(tests_dir)],
        capture_output=True,
        text=True,
    )
    assert result_black.returncode == 0, (
        f"black check failed:\n{result_black.stderr}\n{result_black.stdout}"
    )