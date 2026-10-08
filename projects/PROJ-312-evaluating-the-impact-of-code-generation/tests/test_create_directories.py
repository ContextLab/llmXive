import os
import shutil
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
# Note: In a real execution environment, this would be handled by the runner
# For this test, we assume the module is importable from the code directory
sys.path.insert(0, str(Path(__file__).parent.parent / "projects/PROJ-312-evaluating-the-impact-of-code-generation" / "code"))

def test_directory_creation():
    """
    Test that the create_directories script creates the required structure.
    """
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        # We need to modify the script to work in a temp directory for testing
        # Since we can't easily modify the script, we'll just verify the logic
        # by checking that the directories would be created.
        
        # Instead, we'll run the actual script in the temp directory
        # by temporarily changing the working directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Import and run the script
            import create_directories
            result = create_directories.main()
            
            # Check that the script returned success
            assert result == 0, "Script returned non-zero exit code"
            
            # Verify that the directories were created
            project_root = Path(tmpdir) / "projects/PROJ-312-evaluating-the-impact-of-code-generation"
            assert project_root.exists(), "Project root directory was not created"
            
            # Check specific subdirectories
            required_dirs = [
                "code",
                "data",
                "data/raw",
                "data/processed",
                "data/spot_check",
                "tests",
                "contracts",
                "artifacts",
                "state",
                "logs"
            ]
            
            for subdir in required_dirs:
                dir_path = project_root / subdir
                assert dir_path.exists(), f"Directory {dir_path} was not created"
                assert dir_path.is_dir(), f"{dir_path} is not a directory"
        finally:
            os.chdir(original_cwd)