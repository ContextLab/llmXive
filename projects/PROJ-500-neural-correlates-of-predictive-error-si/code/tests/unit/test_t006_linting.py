import os
import subprocess
import sys
from pathlib import Path
import pytest


@pytest.fixture
def project_root():
    """Return the root of the project (parent of code/)."""
    return Path(__file__).resolve().parent.parent.parent


def test_ruff_config_exists(project_root):
    """Verify ruff.toml exists in the project root."""
    ruff_path = project_root / "ruff.toml"
    assert ruff_path.exists(), f"ruff.toml not found at {ruff_path}"
    content = ruff_path.read_text()
    assert "[lint]" in content, "ruff.toml must contain [lint] section"


def test_black_config_exists(project_root):
    """Verify black configuration exists in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"


def test_ruff_lint_passes(project_root):
    """Run ruff check on the code directory to ensure no linting errors."""
    code_dir = project_root / "code"
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    # We expect success (return code 0). If there are linting errors, this will fail.
    assert result.returncode == 0, (
        f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_black_format_check(project_root):
    """Run black --check to ensure code is formatted correctly."""
    code_dir = project_root / "code"
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    # We expect success (return code 0). If formatting is off, this will fail.
    assert result.returncode == 0, (
        f"Black format check failed:\n{result.stdout}\n{result.stderr}"
    )