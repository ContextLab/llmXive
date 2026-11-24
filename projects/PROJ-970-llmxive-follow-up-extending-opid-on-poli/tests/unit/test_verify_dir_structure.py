"""
Unit test for the ``verify_dir_structure`` script.

The test invokes the script's ``main`` function, which creates
``data/processed/dir_structure.txt``. The test then reads the file and
asserts that the expected top‑level directories are present.
"""
import os
from pathlib import Path

import pytest

# Import the script as a module; this will run the ``main`` function.
from code.verify_dir_structure import main as verify_main

@pytest.fixture(scope="module")
def dir_structure_file(tmp_path_factory):
    """
    Runs the verification script and returns the path to the generated
    ``dir_structure.txt`` file.
    """
    # Ensure a clean state: remove any existing file.
    output_path = Path(__file__).parents[2] / "data" / "processed" / "dir_structure.txt"
    if output_path.exists():
        output_path.unlink()

    # Execute the script.
    verify_main()

    # Verify the file was created.
    assert output_path.is_file(), "dir_structure.txt was not created"
    return output_path

def test_dir_structure_contains_expected_entries(dir_structure_file: Path):
    """
    Checks that the generated directory listing includes the required
    top‑level directories created by task T001.
    """
    content = dir_structure_file.read_text()

    # Expected top‑level directories (relative to the repo root)
    expected_dirs = [
        "src",
        "src/environment",
        "src/agent",
        "src/simulation",
        "src/analysis",
        "src/utils",
        "tests",
        "data",
        "data/raw",
        "data/raw/synthetic_graphs",
        "data/processed",
    ]

    for expected in expected_dirs:
        assert expected in content, f"Missing expected directory entry: {expected}"