"""
Unit test for T001 – verifies that the required project directories exist.
"""
import os
from pathlib import Path

def test_directories_created():
    required_dirs = [
        Path("code"),
        Path("data/raw"),
        Path("data/interim"),
        Path("data/processed"),
        Path("docs"),
        Path("tests"),
    ]

    missing = [str(d) for d in required_dirs if not d.is_dir()]
    assert not missing, f"The following required directories are missing: {', '.join(missing)}"