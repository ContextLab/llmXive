"""
test_scaffolding.py

Unit tests that verify the project scaffolding required for task T001.
The tests check that the expected directories and ``__init__`` files exist.
"""

import os
from pathlib import Path

# List of directories that must exist
REQUIRED_DIRS = [
    Path("data/raw"),
    Path("data/processed"),
    Path("data/results"),
    Path("code"),
    Path("code/utils"),
    Path("code/tests"),
    Path("results/paper_figures"),
]

# List of __init__ files that must exist
REQUIRED_INIT_FILES = [
    Path("code/__init__.py"),
    Path("code/utils/__init__.py"),
    Path("code/tests/__init__.py"),
]

def test_directories_exist():
    """All required directories should exist."""
    missing = [str(d) for d in REQUIRED_DIRS if not d.is_dir()]
    assert not missing, f"Missing required directories: {missing}"

def test_init_files_exist():
    """All required __init__.py files should exist."""
    missing = [str(f) for f in REQUIRED_INIT_FILES if not f.is_file()]
    assert not missing, f"Missing required __init files: {missing}"