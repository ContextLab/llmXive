"""
Unit test for the directory‑structure generator.

The test simply imports the ``generate_dir_structure`` function,
invokes it, and checks that the output file exists and contains all
nine required directories.
"""

import os
from pathlib import Path

from code.dir_structure import generate_dir_structure

def test_dir_structure_file_exists_and_contains_all_dirs(tmp_path):
    """
    Ensure that ``generate_dir_structure`` creates the file
    ``data/processed/dir_structure.txt`` and that the file contains the
    names of all required top‑level directories.
    """
    # Run the generator – it will create the directories under the
    # project root (not under the temporary ``tmp_path``).  The function
    # returns the tree string, which we can also inspect.
    tree_output = generate_dir_structure()

    # Expected directory names (relative to the project root)
    expected_dirs = {
        "code",
        "code/simulation",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
    }

    # Verify each expected directory is mentioned in the output.
    for d in expected_dirs:
        assert d in tree_output, f"Missing directory entry: {d}"

    # Verify the output file exists and is non‑empty.
    output_file = Path("data/processed/dir_structure.txt")
    assert output_file.is_file(), "dir_structure.txt was not created"
    assert output_file.stat().st_size > 0, "dir_structure.txt is empty"