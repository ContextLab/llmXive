"""
Tests for the project setup script.
Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
import pytest
from unittest.mock import patch
import sys

# Add the code directory to the path to import the setup script
# Assuming this test runs from the project root or tests directory
code_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from setup_project import create_directory_structure

def test_create_directory_structure():
    """Test that create_directory_structure creates the expected folders."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as temp_root:
        # Run the function
        create_directory_structure(temp_root)
        
        # Define expected directories relative to temp_root
        expected_dirs = [
            "code",
            "data",
            "tests",
            "state",
            "data/raw",
            "data/processed",
            "data/artifacts"
        ]
        
        for subdir in expected_dirs:
            full_path = os.path.join(temp_root, subdir)
            assert os.path.isdir(full_path), f"Directory {full_path} was not created"
            # Check for .gitkeep
            gitkeep_path = os.path.join(full_path, ".gitkeep")
            assert os.path.isfile(gitkeep_path), f".gitkeep missing in {full_path}"

def test_idempotent_creation():
    """Test that running the function twice does not raise errors."""
    with tempfile.TemporaryDirectory() as temp_root:
        # First run
        create_directory_structure(temp_root)
        # Second run
        create_directory_structure(temp_root)
        
        # Verify structure still exists
        assert os.path.isdir(os.path.join(temp_root, "code"))
        assert os.path.isdir(os.path.join(temp_root, "data"))