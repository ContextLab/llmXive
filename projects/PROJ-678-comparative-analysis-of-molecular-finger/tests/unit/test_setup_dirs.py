"""
Unit tests for the setup_dirs script.
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the script we just created
from code.setup_dirs_t001a import main as setup_dirs_main

def test_directory_creation(tmp_path):
    """Test that the script creates the required directories and .gitkeep files."""
    # Run the setup script with a temporary repository root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        # Simulate repository layout: create a dummy 'projects' folder so the script can place its output there
        (tmp_path / "projects").mkdir()

        # Run the main function
        setup_dirs_main()

        # Expected base path of the new project
        base = tmp_path / "projects" / "PROJ-678-comparative-analysis-of-molecular-fingerprints"

        # Verify top‑level directories
        for sub in ["data/raw", "data/processed", "code", "tests"]:
            assert (base / sub).exists(), f"Missing directory: {sub}"

        # Verify .gitkeep files
        assert (base / "data/raw/.gitkeep").exists()
        assert (base / "data/processed/.gitkeep").exists()

    finally:
        os.chdir(original_cwd)