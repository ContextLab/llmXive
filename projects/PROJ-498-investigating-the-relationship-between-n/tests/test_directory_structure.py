"""
Unit test for T001 – verifies that the required directory structure exists.
The test should pass after running `code/create_directories.py`.
"""
from pathlib import Path

def test_required_directories_exist():
    base = Path("projects/PROJ-498-investigating-the-relationship-between-n")
    assert base.is_dir(), f"Base directory {base} does not exist"

    for sub in ["code", "data", "tests"]:
        sub_path = base / sub
        assert sub_path.is_dir(), f"Required subdirectory {sub_path} does not exist"