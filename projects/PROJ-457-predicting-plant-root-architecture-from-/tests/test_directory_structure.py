"""
test_directory_structure.py
---------------------------
Verify that `directory_structure.txt` exists and lists all required
directories, and that each listed directory actually exists on disk.
"""

import pathlib


def test_directory_structure_file_exists():
    """The file must exist at the project root."""
    file_path = pathlib.Path(__file__).parents[2] / "directory_structure.txt"
    assert file_path.is_file(), f"{file_path} does not exist"


def test_directories_listed_and_exist():
    """Each directory listed in the file must exist."""
    root = pathlib.Path(__file__).parents[2]
    file_path = root / "directory_structure.txt"
    with file_path.open() as f:
        lines = [line.strip() for line in f if line.strip()]

    # Expected relative directory paths (as written by the script)
    expected = {
        "code/",
        "tests/",
        "data/raw/",
        "data/processed/",
        "artifacts/",
        "artifacts/logs/",
    }

    assert set(lines) == expected, f"directory_structure.txt contents mismatch: {lines}"

    # Verify each directory exists
    for rel in expected:
        dir_path = root / rel
        assert dir_path.is_dir(), f"Required directory missing: {dir_path}"
