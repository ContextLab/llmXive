import pathlib
from code.check_skeleton import missing_directories

def test_skeleton_directories():
    """Verify that all required top‑level directories exist."""
    expected_dirs = [
        pathlib.Path("src"),
        pathlib.Path("tests"),
        pathlib.Path("data"),
        pathlib.Path("results"),
        pathlib.Path("docs"),
        pathlib.Path("contracts"),
    ]
    missing = missing_directories(expected=expected_dirs, root=pathlib.Path.cwd())
    assert missing == [], f"Missing required directories: {missing}"