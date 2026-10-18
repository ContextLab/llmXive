"""
Unit tests for the ``code.create_structure`` script.

The tests verify that the script has produced the required
``logs/structure.txt`` file and that the file contains at least one
of the expected directory names.
"""

import pathlib


def test_structure_file_exists():
    """The snapshot file must exist and be non‑empty."""
    path = pathlib.Path("logs/structure.txt")
    assert path.is_file(), "logs/structure.txt was not created"
    assert path.stat().st_size > 0, "logs/structure.txt is empty"


def test_structure_contains_some_required_dirs():
    """A simple sanity check that the snapshot mentions a required directory."""
    required = {"src/data", "data/raw", "output/figures"}
    content = pathlib.Path("logs/structure.txt").read_text()
    assert any(req in content for req in required), (
        "logs/structure.txt does not list any of the expected directories"
    )