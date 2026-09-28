"""
tests/test_structure.py

Verifies that the required code directory hierarchy exists.
The test invokes ``create_code_structure.main`` to create the directories
(in case they have not been created yet) and then checks that each expected
path is present on disk.
"""

import sys
from pathlib import Path

import pytest

# Ensure the repository root is on ``sys.path`` so that the module can be imported.
REPO_ROOT = Path(__file__).resolve().parents[2]  # code/tests -> repo root
sys.path.insert(0, str(REPO_ROOT))

from create_code_structure import main as create_structure


@pytest.fixture(autouse=True)
def run_structure_creation():
    """
    Run the directory‑creation script before any test in this module.
    """
    create_structure()


def test_code_directories_exist():
    """
    Assert that all required code directories exist after running the
    ``create_code_structure`` script.
    """
    expected_dirs = [
        REPO_ROOT / "src" / "lib",
        REPO_ROOT / "src" / "metrics",
        REPO_ROOT / "src" / "experiment",
        REPO_ROOT / "src" / "analysis",
        REPO_ROOT / "tests",
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} to exist"
        
    # Additionally check that each directory contains an ``__init__.py`` file.
    for d in expected_dirs:
        init_file = d / "__init__.py"
        assert init_file.is_file(), f"Missing __init__.py in {d}"