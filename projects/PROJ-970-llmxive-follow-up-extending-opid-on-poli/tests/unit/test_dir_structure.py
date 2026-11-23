"""
Verify that the directory‑structure capture file contains all required top‑level
directories.  The test reads ``data/processed/dir_structure.txt`` (produced by
``code/create_hierarchy.py``) and checks that each expected path appears.
"""

import pathlib

import pytest

EXPECTED_DIRS = [
    "src",
    "src/environment",
    "src/agent",
    "src/simulation",
    "src/analysis",
    "src/utils",
    "tests",
    "data/raw/synthetic_graphs",
    "data/processed",
]


def test_dir_structure_contains_expected_entries():
    path = pathlib.Path("data/processed/dir_structure.txt")
    assert path.is_file(), f"{path} does not exist"

    content = path.read_text()
    for expected in EXPECTED_DIRS:
        assert expected in content, f"Missing expected entry '{expected}' in dir_structure.txt"