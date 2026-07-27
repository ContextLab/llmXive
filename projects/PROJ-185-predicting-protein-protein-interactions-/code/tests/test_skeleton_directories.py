"""
Unit test specifically for T001c: verifying skeleton directories exist.
"""
import pathlib
import pytest
from pathlib import Path

REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    "results",
    "docs",
    "contracts",
    "scripts",
    "specs",
    "state",
    "figures",
    ".github/workflows",
]

@pytest.fixture
def project_root():
    # Assumes running from code/tests/
    return Path(__file__).resolve().parent.parent.parent

def test_skeleton_directory_exists(project_root):
    """Asserts that all required skeleton directories exist."""
    missing = []
    for d in REQUIRED_DIRS:
        if not (project_root / d).is_dir():
            missing.append(d)

    assert len(missing) == 0, f"Missing required directories: {missing}"