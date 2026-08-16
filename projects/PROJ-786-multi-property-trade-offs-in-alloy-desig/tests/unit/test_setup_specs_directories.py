import os
import pytest
from pathlib import Path
import shutil
import tempfile
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_specs_directories import create_specs_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_creates_specs_directory_structure(temp_project_root):
    """
    Test that create_specs_directories creates the required directory structure
    and a .gitkeep file within it.
    """
    # Change to the temp directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)

    try:
        # Run the function
        result = create_specs_directories()
        
        assert result is True, "Function should return True on success"

        # Verify the path exists
        expected_path = Path(temp_project_root) / "projects" / "PROJ-786-multi-property-trade-offs-in-alloy-desig" / "specs" / "001-multi-property-trade-offs"
        assert expected_path.exists(), f"Directory {expected_path} was not created"
        assert expected_path.is_dir(), f"{expected_path} exists but is not a directory"

        # Verify .gitkeep exists inside
        gitkeep_path = expected_path / ".gitkeep"
        assert gitkeep_path.exists(), f".gitkeep file was not created at {gitkeep_path}"
        assert gitkeep_path.is_file(), f".gitkeep exists but is not a file"

    finally:
        os.chdir(original_cwd)

def test_idempotent(temp_project_root):
    """
    Test that running the function twice does not raise an error (exist_ok=True).
    """
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)

    try:
        # Run twice
        create_specs_directories()
        result_second = create_specs_directories()
        
        assert result_second is True, "Second run should also return True"
        
        expected_path = Path(temp_project_root) / "projects" / "PROJ-786-multi-property-trade-offs-in-alloy-desig" / "specs" / "001-multi-property-trade-offs"
        assert expected_path.exists()
        
    finally:
        os.chdir(original_cwd)
