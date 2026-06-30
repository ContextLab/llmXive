import os
import shutil
import tempfile
from pathlib import Path
import pytest

from code.setup_project_structure import create_project_structure
from code.config import Config

def test_project_structure_creation():
    """Test that the project structure is created correctly."""
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Call the function
            create_project_structure()
            
            # Verify directories exist
            expected_dirs = [
                "data/stimuli",
                "data/stimuli_metadata",
                "data/responses",
                "data/processed",
                "data/ethics",
                "code/data",
                "code/stimuli",
                "code/participants",
                "code/analysis",
                "tests/unit",
                "tests/integration",
                "tests/contract",
                "docs/ethics"
            ]
            
            for dir_path in expected_dirs:
                full_path = Path(temp_dir) / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory"
        finally:
            os.chdir(original_cwd)

def test_idempotency():
    """Test that running the script twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Run twice
            create_project_structure()
            create_project_structure()
            
            # Verify at least one set exists
            assert (Path(temp_dir) / "data/stimuli").exists()
        finally:
            os.chdir(original_cwd)
