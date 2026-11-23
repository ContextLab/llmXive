import os
from pathlib import Path
import pytest

def test_required_directories_exist():
    """Verify that the core project directories exist."""
    base = Path(__file__).resolve().parent.parent
    required_dirs = [
        "code",
        "data/raw",
        "data/derived",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    for rel in required_dirs:
        path = base / rel
        assert path.exists(), f"Directory {path} does not exist"
        assert path.is_dir(), f"{path} is not a directory"

def test_init_files_exist():
    """Verify __init__.py files exist for package directories."""
    base = Path(__file__).resolve().parent.parent
    package_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/derived",
    ]
    for rel in package_dirs:
        init_path = base / rel / "__init__.py"
        assert init_path.exists(), f"Missing __init__.py in {base / rel}"
