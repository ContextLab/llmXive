"""
tests/unit/test_structure.py
Unit test for T001 – verifies that the required directory hierarchy
exists under ``projects/PROJ-915-llmxive-follow-up-extending-measuring-ep``.
"""

from pathlib import Path

# Base path of the hierarchy (relative to repository root)
BASE_DIR = Path("projects/PROJ-915-llmxive-follow-up-extending-measuring-ep")

# Expected sub‑folders (relative to BASE_DIR)
EXPECTED_SUBFOLDERS = [
    "code",
    "data/raw",
    "data/processed",
    "data/interim",
    "data/results",
    "state",
    "tests/unit",
    "tests/integration",
    "docs",
]

def test_directory_structure_exists():
    """Assert that every required sub‑folder has been created."""
    for sub in EXPECTED_SUBFOLDERS:
        path = BASE_DIR / sub
        assert path.is_dir(), f"Missing expected directory: {path}"
    
    # Also verify that the tree output file was generated
    tree_file = Path("data/results/project_structure.txt")
    assert tree_file.is_file(), "project_structure.txt was not created"
    # Basic sanity check: the file should contain the base directory name
    content = tree_file.read_text(encoding="utf-8")
    assert str(BASE_DIR) in content, "Tree output does not contain the base directory name"