"""
Basic test to verify project structure exists.
"""
import os
from pathlib import Path

def test_project_directories_exist():
    """Verify that the core directories created by T001 exist."""
    base = Path(__file__).parent.parent
    required_dirs = [
        base / "code",
        base / "data",
        base / "tests",
        base / "docs",
        base / "data" / "raw",
        base / "data" / "processed",
    ]
    for d in required_dirs:
        assert d.exists(), f"Directory {d} does not exist"
        assert d.is_dir(), f"{d} is not a directory"

def test_code_files_exist():
    """Verify that key configuration and utility files exist."""
    base = Path(__file__).parent.parent
    files = [
        base / "code" / "config.py",
        base / "code" / "utils" / "logging.py",
        base / "code" / "utils" / "texture.py",
    ]
    for f in files:
        assert f.exists(), f"File {f} does not exist"
