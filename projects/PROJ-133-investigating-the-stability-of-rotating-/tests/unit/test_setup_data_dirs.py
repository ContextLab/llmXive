import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.setup_data_dirs import create_project_structure

def test_create_project_structure():
    """Test that create_project_structure creates the expected directories."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Call the function
            create_project_structure()
            
            # Verify the directories were created
            base_dir = Path("data")
            assert base_dir.exists(), "data directory should exist"
            
            raw_dir = base_dir / "raw"
            assert raw_dir.exists(), "data/raw directory should exist"
            assert raw_dir.is_dir(), "data/raw should be a directory"
            
            processed_dir = base_dir / "processed"
            assert processed_dir.exists(), "data/processed directory should exist"
            assert processed_dir.is_dir(), "data/processed should be a directory"
            
            aggregated_dir = base_dir / "aggregated"
            assert aggregated_dir.exists(), "data/aggregated directory should exist"
            assert aggregated_dir.is_dir(), "data/aggregated should be a directory"
            
        finally:
            os.chdir(original_cwd)

def test_create_project_structure_idempotent():
    """Test that create_project_structure is idempotent (can be called multiple times)."""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Call the function twice
            create_project_structure()
            create_project_structure()
            
            # Verify the directories still exist and haven't been duplicated
            base_dir = Path("data")
            assert base_dir.exists()
            
            raw_dir = base_dir / "raw"
            assert raw_dir.exists()
            assert len(list(base_dir.glob("*"))) == 3  # raw, processed, aggregated
            
        finally:
            os.chdir(original_cwd)
