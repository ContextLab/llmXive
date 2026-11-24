"""
Test that the project scaffold directories exist.
"""
import sys
from pathlib import Path

# Ensure the code directory is on the import path so we can import config
sys.path.append(str(Path(__file__).resolve().parents[2] / "code"))

from config import get_project_root

def test_directories_exist():
    """
    Verify that the required top‑level sub‑folders are present.
    """
    root = get_project_root()
    expected_dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "code",
        root / "tests",
        root / "docs",
    ]
    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} does not exist"