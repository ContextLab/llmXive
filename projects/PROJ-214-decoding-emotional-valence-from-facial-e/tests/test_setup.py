import os
from pathlib import Path

def test_directories_exist():
    """Verify that the core project directories exist."""
    base = Path(".")
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/models",
    ]
    
    for d in required_dirs:
        assert (base / d).exists(), f"Directory {d} does not exist"
        assert (base / d).is_dir(), f"{d} is not a directory"