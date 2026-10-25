from pathlib import Path
from llmxive_toolkit import paths

def test_directory_structure_file():
    """
    Verify that ``docs/directory_structure.txt`` exists and contains a line for
    each of the nine required top‑level directories.
    """
    file_path: Path = paths.docs("directory_structure.txt")
    assert file_path.is_file(), f"{file_path} does not exist"

    content = file_path.read_text().splitlines()
    expected = [
        "src/",
        "tests/",
        "data/",
        "data/raw/",
        "data/processed/",
        "data/results/",
        "docs/",
        "contracts/",
        "config/",
    ]

    for line in expected:
        assert line in content, f"Missing '{line}' in directory_structure.txt"