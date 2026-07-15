import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the setup script
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import main

def test_directory_structure_created():
    """Test that the required directory structure is created."""
    project_root = Path("projects/PROJ-175-statistical-analysis-of-publicly-availab")
    
    # Expected directories
    expected_dirs = [
        project_root / "code",
        project_root / "data",
        project_root / "tests",
    ]
    
    # Run the setup
    main()
    
    # Verify all directories exist
    for directory in expected_dirs:
        assert directory.exists(), f"Directory {directory} was not created"
        assert directory.is_dir(), f"{directory} is not a directory"

def test_directory_permissions():
    """Test that created directories are writable."""
    project_root = Path("projects/PROJ-175-statistical-analysis-of-publicly-availab")
    
    # Run setup first
    main()
    
    # Test write permissions
    for dir_name in ["code", "data", "tests"]:
        test_file = project_root / dir_name / ".test_marker"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            pytest.fail(f"Cannot write to {project_root / dir_name}: {e}")