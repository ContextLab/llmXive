import os
import sys
from pathlib import Path
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project import main

def test_project_structure_creation(tmp_path):
    """
    Test that the setup script creates the required directories
    and generates the project_structure.txt file.
    """
    # Change to tmp directory to avoid polluting the real repo
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Run the main function
        result = main()
        
        assert result == 0, "Setup script should exit with 0"
        
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
        
        for d in required_dirs:
            assert Path(d).is_dir(), f"Directory {d} was not created"
        
        # Verify output file exists
        assert Path("project_structure.txt").is_file(), "project_structure.txt was not created"
        
        # Verify content is not empty
        content = Path("project_structure.txt").read_text()
        assert len(content) > 0, "project_structure.txt is empty"
        
    finally:
        os.chdir(original_cwd)