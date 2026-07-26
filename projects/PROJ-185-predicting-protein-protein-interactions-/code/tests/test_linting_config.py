import subprocess
import os
import sys
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent

def test_ruff_check_passes(project_root):
    """Verify that ruff check passes on the project codebase."""
    ruff_path = project_root / ".ruff.toml"
    assert ruff_path.exists(), ".ruff.toml configuration file missing"

    # Run ruff check against the src and tests directories
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src", "tests", "--config", str(ruff_path)],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    # We expect success (exit code 0) if no linting errors are found
    # If ruff is not installed, we skip this specific check but ensure the config exists
    if result.returncode == 127 or "No module named 'ruff'" in result.stderr:
        pytest.skip("ruff not installed in environment, skipping lint check execution")

    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_check_passes(project_root):
    """Verify that black check passes on the project codebase."""
    # Run black --check against the src and tests directories
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--config", str(project_root / "pyproject.toml"), "src", "tests"],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    if result.returncode == 127 or "No module named 'black'" in result.stderr:
        pytest.skip("black not installed in environment, skipping format check execution")

    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"