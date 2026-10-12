"""
tests/unit/test_structure.py
Unit test for T001 – verifies that the required directory hierarchy
exists under ``projects/PROJ-915-llmxive-follow-up-extending-measuring-ep``.

Note: the top-level ``state/`` directory is owned by the platform, so it
is deliberately NOT part of the project-owned hierarchy checked here.
"""

from pathlib import Path

from llmxive_toolkit import paths

# Expected sub-foldolders (relative to the project root)
EXPECTED_SUBFOLDERS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "data/results",
    "tests/unit",
    "tests/integration",
    "docs",
]


def test_directory_structure_exists():
    """Assert that every required sub-folder has been created."""
    root = paths.root
    for sub in EXPECTED_SUBFOLDERS:
        path = root / sub
        assert path.is_dir(), f"Missing expected directory: {path}"

    # Also verify that the tree output file was generated
    tree_file = paths.data("results", "project_structure.txt")
    assert tree_file.is_file(), "project_structure.txt was not created"
    # Basic sanity check: the file should contain the base directory name
    content = tree_file.read_text(encoding="utf-8")
    assert "PROJ-915-llmxive-follow-up-extending-measuring-ep" in content, (
        "Tree output does not contain the base directory name"
    )