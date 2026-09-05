import os
import shutil
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from create_project_structure import ensure_directory, main

@pytest.fixture
def temp_base_dir():
    """Create a temporary base directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_ensure_directory_creates_new(temp_base_dir):
    """Test that ensure_directory creates a new directory."""
    test_path = temp_base_dir / "new_dir"
    assert not test_path.exists()
    
    # Call the function (we need to adjust the path logic for testing)
    # Since ensure_directory takes a string path, we pass the absolute path
    ensure_directory(str(test_path))
    
    assert test_path.exists()
    assert test_path.is_dir()

def test_ensure_directory_exists_noop(temp_base_dir):
    """Test that ensure_directory does nothing if directory exists."""
    test_path = temp_base_dir / "existing_dir"
    test_path.mkdir(parents=True)
    
    assert test_path.exists()
    
    # Call the function
    ensure_directory(str(test_path))
    
    # Should still exist and be a directory
    assert test_path.exists()
    assert test_path.is_dir()

def test_main_creates_all_directories(temp_base_dir):
    """Test that main creates all required directories."""
    # Change to temp directory to simulate repo root
    # The main function uses relative paths, so we run it in the temp dir
    original_cwd = os.getcwd()
    os.chdir(str(temp_base_dir))
    
    try:
        # Call main
        main()
        
        # Define expected paths
        base_path = Path("projects/PROJ-967-llmxive-follow-up-extending-beyond-scala")
        
        expected_dirs = [
            base_path / "data" / "raw",
            base_path / "data" / "processed",
            base_path / "results",
            base_path / "code",
            base_path / "tests",
        ]
        
        # Verify all directories were created
        for dir_path in expected_dirs:
            full_path = temp_base_dir / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
    finally:
        os.chdir(original_cwd)