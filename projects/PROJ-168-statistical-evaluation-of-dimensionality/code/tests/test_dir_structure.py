"""
Test that the directory tree required by T001 exists and that the
``results/dir_listing.txt`` file contains each of the expected directories.
"""
import pathlib

def test_directories_and_listing():
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/embeddings",
        "data/clustering",
        "data/metrics",
        "data/results",
        "figures",
        "results",
        "code",
        "code/tests",
        "paper",
        ".github/workflows",
    ]

    # Verify that each required directory exists.
    for d in required_dirs:
        assert pathlib.Path(d).is_dir(), f"Missing required directory: {d}"

    # Verify the listing file exists and contains each required directory.
    listing_path = pathlib.Path("results/dir_listing.txt")
    assert listing_path.is_file(), "results/dir_listing.txt was not created"

    listed = set(line.strip() for line in listing_path.read_text().splitlines() if line.strip())
    for d in required_dirs:
        assert d in listed, f"Directory {d} not present in dir_listing.txt"