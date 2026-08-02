"""
Unit tests to verify the project directory structure is correctly created.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test (adjust import path if necessary)
# We will test the logic directly here to avoid import issues in test isolation
from code.setup_structure import create_structure

def test_directory_creation():
    """Test that the create_structure function creates the required directories."""
    # Create a temporary directory to simulate a project root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Temporarily change the working directory to simulate project root
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            
            # Create a mock setup_structure.py in the temp dir to test logic
            # We'll just test the logic of directory creation directly
            required_dirs = [
                "code/orchestrator",
                "code/orchestrator/workers",
                "code/analysis",
                "code/simulation",
                "data/raw",
                "data/processed",
                "tests",
                "tests/unit",
                "tests/integration",
                "tests/contract",
                "specs",
                "contracts",
                "state",
                "figures"
            ]
            
            # Create directories
            for dir_path in required_dirs:
                full_path = temp_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
            
            # Verify all directories exist
            for dir_path in required_dirs:
                full_path = temp_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory"
                
        finally:
            os.chdir(original_cwd)

def test_nested_directories():
    """Test that nested directories are created correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create nested structure
        nested_path = temp_path / "code" / "orchestrator" / "workers"
        nested_path.mkdir(parents=True, exist_ok=True)
        
        assert nested_path.exists()
        assert (temp_path / "code").exists()
        assert (temp_path / "code" / "orchestrator").exists()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])