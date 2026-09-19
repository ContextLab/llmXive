import os
from pathlib import Path
import pytest

def test_required_directories_exist():
    """
    Verify that the standard project directories exist after setup.
    """
    root = Path(".")
    
    required_dirs = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "tests",
    ]

    for d in required_dirs:
        assert d.exists(), f"Required directory {d} does not exist."
        assert d.is_dir(), f"Path {d} exists but is not a directory."