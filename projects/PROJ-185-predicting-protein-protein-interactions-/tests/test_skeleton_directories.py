"""Test that the repository skeleton directories exist after running the
``create_skeleton`` script.

The test mirrors the CI step required by task *T001d*: it invokes the
``create_skeleton`` script (which should be idempotent) and then asserts
that each required top‑level directory is present.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def run_skeleton():
    """Run the skeleton‑creation script once for the whole test session."""
    result = subprocess.run(
        [sys.executable, "code/create_skeleton.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Skeleton creation failed: {result.stderr}"
    return result


def test_skeleton_directories_exist(run_skeleton):
    """Assert that each required directory now exists."""
    required = ["src", "tests", "data", "results", "docs", "contracts"]
    for d in required:
        assert Path(d).is_dir(), f"Required directory '{d}' is missing"


def test_check_skeleton_script(run_skeleton):
    """The helper script used by CI must also succeed."""
    result = subprocess.run(
        [sys.executable, "code/check_skeleton.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"check_skeleton failed: {result.stderr}"
    assert "All skeleton directories are present." in result.stdout