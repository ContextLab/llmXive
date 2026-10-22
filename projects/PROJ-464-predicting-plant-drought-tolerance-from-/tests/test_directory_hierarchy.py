"""
Unit test for task T001a.

After ``code/create_hierarchy.py`` has been executed, this test checks that
each of the required top‑level directories exists on disk.
"""

import pathlib

def test_required_directories_exist():
    # Resolve the repository root (two levels up from this test file).
    project_root = pathlib.Path(__file__).resolve().parents[2]

    expected_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "code",
        project_root / "tests",
        project_root / "docs",
        project_root / "state",
        project_root / "contracts",
        project_root / "results",
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Required directory missing: {d}"