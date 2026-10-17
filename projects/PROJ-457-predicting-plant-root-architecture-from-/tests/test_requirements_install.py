"""Verify that code/requirements.txt exists and pip can resolve it.

The previous version of this test built the path from a hardcoded
runner directory that did not match the project layout, causing the
CI step to fail with exit code 1 even though the file existed. This
version locates the file relative to the repository (project) root,
which is robust to wherever the checkout lives.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = PROJECT_ROOT / "code" / "requirements.txt"


def test_requirements_file_exists():
    assert REQUIREMENTS.is_file(), f"Missing {REQUIREMENTS}"


def test_requirements_are_pinned():
    """Every non-comment, non-empty line must pin an exact version."""
    assert REQUIREMENTS.is_file()
    lines = [
        ln.strip()
        for ln in REQUIREMENTS.read_text().splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    assert lines, "requirements.txt is empty"
    for ln in lines:
        assert "==" in ln, f"Dependency not exactly pinned: {ln}"


def test_pip_install_requirements_succeeds():
    """Run pip install -r against the real file; must exit 0."""
    assert REQUIREMENTS.is_file()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(REQUIREMENTS),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"pip install failed (rc={result.returncode}):\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )