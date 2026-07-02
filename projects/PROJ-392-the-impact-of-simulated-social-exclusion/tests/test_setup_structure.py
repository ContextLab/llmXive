"""
Tests for the project setup structure script.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We need to ensure the code directory is in the path
import sys
from pathlib import Path

# Add the 'code' directory to sys.path if it's not already there
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project_structure import create_directories

def test_create_directories():
    """Test that create_directories creates the expected directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Define expected directories
        expected_dirs = [
            "data/raw-fmri",
            "data/processed-fmri",
            "data/behavioral",
            "data/results",
            "code/manipulation",
            "code/utils",
            "code/data_download",
            "code/preprocess",
            "code/analysis",
            "code/visualization",
            "code/pipeline",
        ]
        
        # Run the function
        create_directories(root)
        
        # Verify each directory was created
        for dir_path in expected_dirs:
            full_path = root / dir_path
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

def test_create_directories_idempotent():
    """Test that running create_directories twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        
        # Run twice
        create_directories(root)
        create_directories(root)
        
        # Verify directories still exist
        expected_dirs = [
            "data/raw-fmri",
            "data/behavioral",
            "code/manipulation",
            "code/utils",
        ]
        
        for dir_path in expected_dirs:
            assert (root / dir_path).exists()