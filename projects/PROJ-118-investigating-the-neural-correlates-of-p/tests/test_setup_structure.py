import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
import sys
# We assume the test runs from the project root or we add the parent to path
# If running via pytest from root, code/ is a sibling to tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from setup_project_structure import setup_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate the project root."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

def test_setup_directories_creates_folders(temp_project_root):
    """Test that setup_directories creates the required folder structure."""
    # Change to the temp directory to simulate running the script there
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run the setup function
        created = setup_directories()
        
        # Verify the required directories exist
        required_dirs = ["data/raw", "data/processed", "code", "tests", "results"]
        for dir_name in required_dirs:
            dir_path = temp_project_root / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"
        
        # Verify .gitkeep files exist in data directories
        for data_dir in ["data/raw", "data/processed"]:
            gitkeep_path = temp_project_root / data_dir / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep missing in {data_dir}"
            assert gitkeep_path.is_file(), f".gitkeep in {data_dir} is not a file"
        
        # Verify __init__.py exists in tests (created by setup_directories logic)
        tests_init = temp_project_root / "tests" / "__init__.py"
        assert tests_init.exists(), "tests/__init__.py was not created"

    finally:
        os.chdir(original_cwd)

def test_setup_directories_idempotent(temp_project_root):
    """Test that running setup_directories twice does not error."""
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Run twice
        setup_directories()
        setup_directories()
        
        # Verify directories still exist
        assert (temp_project_root / "data" / "raw").exists()
        assert (temp_project_root / "data" / "processed").exists()
        
    finally:
        os.chdir(original_cwd)