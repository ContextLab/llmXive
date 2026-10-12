"""
Verify that the project skeleton required by T001 exists and that
``ruff`` reports no linting errors.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def project_root() -> Path:
    """Root directory of the repository (where this test lives)."""
    return Path(__file__).resolve().parents[1]


def test_directories_exist(project_root: Path) -> None:
    """Check that the essential top‑level directories are present."""
    required_dirs = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "docs",
        project_root / "tests",
    ]
    for d in required_dirs:
        assert d.is_dir(), f"Required directory missing: {d}"


def test_ruff_linting_passes(project_root: Path) -> None:
    """
    Run ``ruff check .`` from the repository root and assert that it
    exits with a status code of 0 (no linting errors).
    """
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, f"Ruff linting failed:\n{result.stdout}"