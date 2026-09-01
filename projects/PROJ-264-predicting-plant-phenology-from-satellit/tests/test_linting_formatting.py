import subprocess
import sys
import os
from pathlib import Path
import pytest

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

@pytest.mark.skipif(sys.platform == "win32", reason="Skip on Windows for CI compatibility")
def test_ruff_check_passes():
    """Verify that ruff check passes on the codebase."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(project_root / "code")],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        # If ruff is not installed, we skip the test or fail loudly depending on env
        # For this task, we assume ruff is in the environment or installed via requirements
        if result.returncode != 0:
            pytest.fail(f"Ruff check failed:\n{result.stdout}\n{result.stderr}")
    except FileNotFoundError:
        pytest.skip("Ruff not found in environment")

@pytest.mark.skipif(sys.platform == "win32", reason="Skip on Windows for CI compatibility")
def test_black_check_passes():
    """Verify that black check (diff) passes on the codebase."""
    project_root = get_project_root()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "--diff", str(project_root / "code")],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode != 0:
            pytest.fail(f"Black check failed:\n{result.stdout}\n{result.stderr}")
    except FileNotFoundError:
        pytest.skip("Black not found in environment")

@pytest.mark.skipif(sys.platform == "win32", reason="Skip on Windows for CI compatibility")
def test_ruff_format_check_passes():
    """Verify that ruff format check passes (if ruff format is supported)."""
    project_root = get_project_root()
    try:
        # Check if ruff format command exists
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "format", "--check", str(project_root / "code")],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode != 0:
            # Some older ruff versions might not have format command
            if "error: unrecognized subcommand" in result.stderr:
                pytest.skip("Ruff format not supported in this version")
            pytest.fail(f"Ruff format check failed:\n{result.stdout}\n{result.stderr}")
    except FileNotFoundError:
        pytest.skip("Ruff not found in environment")