import os
import pytest
from pathlib import Path
import shutil

def test_spec_directory_exists():
    """
    Test that the specific spec directory required by T001c exists.
    """
    # The directory should be created relative to the current working directory
    # where the setup script was run (or the project root).
    # We check for the existence of the path.
    spec_dir = Path.cwd() / "specs" / "001-neural-correlates-of-anticipatory-reward"
    assert spec_dir.exists(), f"Spec directory {spec_dir} does not exist."
    assert spec_dir.is_dir(), f"{spec_dir} exists but is not a directory."

def test_other_directories_exist():
    """
    Test that other directories created by T001a and T001b also exist.
    """
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/figures"
    ]
    for dir_name in required_dirs:
        dir_path = Path.cwd() / dir_name
        assert dir_path.exists(), f"Required directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"{dir_path} exists but is not a directory."