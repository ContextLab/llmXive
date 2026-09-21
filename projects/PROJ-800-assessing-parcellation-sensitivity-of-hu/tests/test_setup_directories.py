import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to import the function, but since the code is in 'code/', 
# we adjust the path or assume the test runner adds 'code/' to sys.path.
# For this implementation, we assume the test is run from the project root
# and the 'code' directory is in the path, or we import via relative logic.
# However, to be safe and standard, we will import the logic directly.

# Add 'code' to path for imports if running as script
import sys
from pathlib import Path
current_dir = Path(__file__).parent.parent
code_dir = current_dir / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_directories import ensure_directory, main

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_ensure_directory_creates_new(temp_project_root):
    """Test that ensure_directory creates a new directory."""
    new_dir = temp_project_root / "new_dir" / "sub_dir"
    ensure_directory(new_dir)
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_ensure_directory_exists(temp_project_root):
    """Test that ensure_directory does not fail if directory exists."""
    existing_dir = temp_project_root / "existing"
    existing_dir.mkdir()
    # Should not raise
    ensure_directory(existing_dir)
    assert existing_dir.exists()

def test_main_creates_structure(temp_project_root):
    """Test that main() creates the expected directory structure."""
    # Change to temp root so relative paths resolve correctly
    os.chdir(temp_project_root)
    
    result = main()
    
    assert result == 0, "main() should return 0 on success"
    
    expected_dirs = [
        "projects/PROJ-800-assessing-parcellation-sensitivity-of-hu",
        "projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/code",
        "projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/tests",
        "projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data",
        "projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/raw",
        "projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/processed",
        "projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/results",
    ]
    
    for dir_path in expected_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} was not created"
        assert full_path.is_dir(), f"{dir_path} is not a directory"