"""
Test suite for ``code/create_project_tree.py``.
It verifies that the required directories are created and that the
``results/dir_listing.txt`` file contains each of them.
"""

import sys
from pathlib import Path

import pytest

# The script resides in ``code/create_project_tree.py``; import it.
# Adding the repository root to ``sys.path`` ensures the import works.
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from create_project_tree import main as init_project

REQUIRED_DIRS = [
    Path("data/raw"),
    Path("data/processed"),
    Path("data/embeddings"),
    Path("data/clustering"),
    Path("data/metrics"),
    Path("data/results"),
    Path("figures"),
    Path("code"),
    Path("code/tests"),
    Path("paper"),
]


def test_create_project_tree(tmp_path, monkeypatch):
    """
    Run the initialisation script in a temporary directory and check that
    all required directories exist and that the listing file contains them.
    """
    # Switch the working directory to a temporary location.
    monkeypatch.chdir(tmp_path)

    # Execute the script.
    init_project()

    # Verify that each required directory now exists.
    for d in REQUIRED_DIRS:
        assert (tmp_path / d).is_dir(), f"Missing directory: {d}"

    # Verify the listing file.
    listing_path = tmp_path / "results" / "dir_listing.txt"
    assert listing_path.is_file(), "results/dir_listing.txt was not created"

    listing_content = listing_path.read_text(encoding="utf-8")
    for d in REQUIRED_DIRS:
        assert str(d) in listing_content, f"Directory {d} not listed in dir_listing.txt"