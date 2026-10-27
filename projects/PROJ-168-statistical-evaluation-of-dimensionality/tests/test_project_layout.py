"""
Test that the project layout has been initialised correctly.

The test checks:
1. That ``results/dir_listing.txt`` exists.
2. That the file contains each of the required directories.
"""
import pathlib

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/embeddings",
    "data/clustering",
    "data/metrics",
    "data/results",
    "figures",
    "code",
    "code/tests",
    "paper",
]

def test_dir_listing_exists():
    listing_path = pathlib.Path("results/dir_listing.txt")
    assert listing_path.is_file(), "results/dir_listing.txt should exist"

def test_all_required_dirs_present_in_listing():
    listing_path = pathlib.Path("results/dir_listing.txt")
    lines = [line.strip() for line in listing_path.read_text().splitlines() if line.strip()]

    # ``find`` returns paths relative to the project root.
    # Ensure each required directory appears exactly as listed.
    missing = [d for d in REQUIRED_DIRS if d not in lines]
    assert not missing, f"The following required directories are missing from dir_listing.txt: {missing}"