import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the function. Since setup_project.py is in code/,
# and tests are in tests/, we need to add the parent or code to path.
# However, standard practice in these pipelines often assumes running from root
# or adjusting sys.path. Let's assume we can import from code.setup_project
# if code/ is in the python path, or we import the function directly by adding path.

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to simulate the project root."""
    return tmp_path

def test_project_structure_creation(temp_project_root):
    """
    Test that setup_project creates the required directories and project_structure.txt.
    """
    # Change to the temp directory to simulate running the script in the project root
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)

    try:
        # Import the main function
        # We need to add the 'code' directory to sys.path to import setup_project
        # But setup_project.py is IN code/, so we import from code.setup_project
        # Wait, the file is at code/setup_project.py.
        # To import it, we need the parent of 'code' in sys.path.
        # Since we are in temp_project_root, and code/ is a subdirectory:
        sys.path.insert(0, str(temp_project_root))
        
        from code.setup_project import main

        # Run the function
        result = main()
        
        assert result == 0, "main() should return 0 on success"

        # Verify directories exist
        required_dirs = [
            "code/utils",
            "data/raw",
            "data/processed",
            "data/results",
            "data/metadata",
            "tests/unit",
            "tests/integration",
            "docs"
        ]

        for dir_path in required_dirs:
            full_path = temp_project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"

        # Verify project_structure.txt exists
        output_file = temp_project_root / "project_structure.txt"
        assert output_file.exists(), "project_structure.txt should be created"
        assert output_file.is_file(), "project_structure.txt should be a file"

        # Verify content is not empty
        content = output_file.read_text()
        assert len(content) > 0, "project_structure.txt should not be empty"
        assert "Summary:" in content, "project_structure.txt should contain a summary"
        assert "code/utils" in content, "project_structure.txt should list code/utils"

    finally:
        # Restore original working directory and sys.path
        os.chdir(original_cwd)
        if str(temp_project_root) in sys.path:
            sys.path.remove(str(temp_project_root))