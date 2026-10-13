"""
Unit test for the quick‑start documentation.

This test verifies two things:
1. The top‑level README lists the required project folders.
2. The quick‑start guide contains the exact verification command
   `python -m code.main --mode verification`.
"""

import pathlib

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_readme_contains_top_level_folders():
    readme_path = PROJECT_ROOT / "README.md"
    assert readme_path.is_file(), "README.md not found at project root"
    content = readme_path.read_text()
    for folder in ("code/", "data/", "tests/"):
        assert folder in content, f"Folder '{folder}' missing from README.md"


def test_quickstart_contains_verification_command():
    quickstart_path = PROJECT_ROOT / "quickstart.md"
    assert quickstart_path.is_file(), "quickstart.md not found at project root"
    content = quickstart_path.read_text()
    expected_cmd = "python -m code.main --mode verification"
    assert expected_cmd in content, f"Verification command '{expected_cmd}' not found in quickstart.md"