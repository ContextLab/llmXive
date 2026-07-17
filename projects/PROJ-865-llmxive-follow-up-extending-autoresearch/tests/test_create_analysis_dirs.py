import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.setup.create_analysis_dirs import create_directory_structure

def test_create_directory_structure_exists():
    """Test that the directory is created if it does not exist."""
    # Determine the expected path relative to the project root
    expected_dir = project_root / "code" / "04_analysis"
    
    # Remove if exists to test creation (only if it's a test temp dir or we are sure)
    # Since this is a setup task, we assume the directory might not exist.
    # We will check existence, run the function, and verify.
    
    # If it already exists, we just verify it's a directory
    if expected_dir.exists():
        assert expected_dir.is_dir(), f"Expected {expected_dir} to be a directory"
    else:
        # Run the function
        result_path = create_directory_structure()
        assert Path(result_path).is_dir(), f"Directory {result_path} was not created"
        assert expected_dir.is_dir(), f"Expected directory {expected_dir} does not exist"

def test_create_directory_structure_idempotent():
    """Test that running the function twice does not raise an error."""
    result_path = create_directory_structure()
    result_path_2 = create_directory_structure()
    assert result_path == result_path_2
    assert Path(result_path).is_dir()