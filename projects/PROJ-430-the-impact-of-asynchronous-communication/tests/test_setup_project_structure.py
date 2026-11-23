"""
Tests for setup_project_structure.py (T001a, T001b, T006).

Verifies that the directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add code directory to path to import the module
current_dir = Path(__file__).parent
code_dir = current_dir.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_project_structure import main, ensure_directory_exists

def test_directory_creation_in_temp():
    """
    Test that the script creates the expected directory structure 
    in a temporary directory to avoid polluting the real workspace during testing.
    """
    # Create a temporary directory to simulate the repo root
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Manually construct the paths we expect the script to create
        # We modify the script's behavior slightly for testing by passing a root,
        # but since the script uses cwd(), we'll run it in the temp_dir
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_path)
            
            # Run the main function
            result = main()
            assert result == 0, "main() should return 0 on success"
            
            # Verify T001a: Project root exists
            project_root = temp_path / "projects" / "PROJ-430-the-impact-of-asynchronous-communication"
            assert project_root.exists(), f"Project root {project_root} was not created"
            assert project_root.is_dir(), f"{project_root} is not a directory"
            
            # Verify T001b: Subdirectories exist
            for subdir in ["code", "data", "tests", "docs"]:
                dir_path = project_root / subdir
                assert dir_path.exists(), f"Subdirectory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"
            
            # Verify T006: Data subdirectories
            data_root = project_root / "data"
            for subdir in ["raw", "derived", "validation", "logs"]:
                dir_path = data_root / subdir
                assert dir_path.exists(), f"Data subdirectory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"
            
            # Verify T006: .gitkeep in validation
            validation_dir = data_root / "validation"
            gitkeep = validation_dir / ".gitkeep"
            assert gitkeep.exists(), f".gitkeep not found in {validation_dir}"
            
            # Verify T006: .gitignore in data
            gitignore = data_root / ".gitignore"
            assert gitignore.exists(), f".gitignore not found in {data_root}"
            content = gitignore.read_text()
            assert "*.csv" in content, ".gitignore missing *.csv pattern"
            assert "*.json" in content, ".gitignore missing *.json pattern"
            assert "!validation/.gitkeep" in content, ".gitignore missing validation exception"
            
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    test_directory_creation_in_temp()
    print("All tests passed.")