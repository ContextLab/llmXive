"""
Test that the quickstart documentation contains the required sections.
This does not execute the pipeline; it merely verifies that the documentation
was updated as part of task T003.
"""

import pathlib

QUICKSTART_PATH = pathlib.Path(__file__).parents[2] / "quickstart.md"


def test_quickstart_contains_layout():
    """The quickstart must describe the project layout."""
    content = QUICKSTART_PATH.read_text()
    assert "Project Layout" in content, "Missing 'Project Layout' section in quickstart.md"
    assert "data/" in content, "Project layout should reference the data folder"
    assert "code/" in content, "Project layout should reference the code folder"


def test_quickstart_contains_dependencies():
    """The quickstart must list the dependencies."""
    content = QUICKSTART_PATH.read_text()
    assert "Dependencies" in content, "Missing 'Dependencies' section in quickstart.md"
    # Check that a few key packages are mentioned
    for pkg in ("numpy", "pandas", "nibabel", "openneuro-py"):
        assert pkg in content, f"Package '{pkg}' not listed in quickstart dependencies"


def test_requirements_match_quickstart():
    """Every line in requirements.txt should appear in the quickstart dependencies block."""
    req_path = pathlib.Path(__file__).parents[2] / "requirements.txt"
    req_lines = [line.strip() for line in req_path.read_text().splitlines() if line.strip()]
    quick_content = QUICKSTART_PATH.read_text()
    for line in req_lines:
        pkg = line.split(">=")[0]
        assert pkg in quick_content, f"Package '{pkg}' from requirements.txt not documented in quickstart.md"