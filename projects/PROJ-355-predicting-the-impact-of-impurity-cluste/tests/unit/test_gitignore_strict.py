import pathlib

def test_gitignore_strict():
    """
    Verify that the project's .gitignore file exists and contains exactly the required lines
    in the correct order, with no trailing spaces.
    """
    # Locate the repository root (two levels up from this test file)
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    gitignore_path = repo_root / ".gitignore"

    assert gitignore_path.is_file(), ".gitignore file not found at project root"

    expected_lines = [
        "data/",
        "results/",
        "*.pyc",
        "__pycache__/",
    ]

    with gitignore_path.open("r") as f:
        # Read lines without newline characters
        lines = [line.rstrip("\n") for line in f]

    assert lines == expected_lines, f".gitignore content mismatch. Expected {expected_lines}, got {lines}"