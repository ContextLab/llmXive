"""
Tests for the project setup script (T001).

These tests verify that the directory structure is created correctly
by the setup script.
"""

import os
import tempfile
from pathlib import Path
import pytest

import sys

# Add the code directory to the path so we can import the setup script
# We simulate the import by adding the parent of the test file's parent (project root)
# to sys.path, then importing the module from the code directory.
# However, since setup_project is a script, we will run it via subprocess or import logic.
# For unit testing purposes here, we will test the logic directly by importing the function
# if we refactor, but for now we test the side effects.

# To test the script logic without running the whole script in a subprocess,
# we can copy the logic into a function or import it if it were a module.
# Since the task requires a script, we will import the function if we extract it,
# or we will run the script in a temporary directory.

# Let's refactor the script slightly in our mind: we assume the logic is in a function `create_directories`.
# But since we are testing the *artifact* created, we will run the script in a temp dir.

from code.setup_project import create_directories, main

def test_create_directories_creates_structure(tmp_path: Path):
    """Test that create_directories creates all required folders."""
    required_dirs = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "specs"
    ]
    
    create_directories(tmp_path)
    
    for dir_name in required_dirs:
        full_path = tmp_path / dir_name
        assert full_path.exists(), f"Directory {dir_name} was not created."
        assert full_path.is_dir(), f"{dir_name} exists but is not a directory."

def test_create_directories_idempotent(tmp_path: Path):
    """Test that running the script twice does not cause errors."""
    create_directories(tmp_path)
    # Run again
    create_directories(tmp_path)
    
    # Verify all still exist
    required_dirs = [
        "src", "tests", "data", "data/raw", "data/processed", 
        "data/results", "specs"
    ]
    for dir_name in required_dirs:
        assert (tmp_path / dir_name).exists()