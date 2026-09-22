import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Import the function from the script
# The script is at code/scripts/setup_data_dirs.py
# We need to add the parent directory to sys.path if not already
# But since we are in code/tests/unit/, and the script is in code/scripts/,
# we might need to adjust the import.
# However, the task says "import only names that exist (in the standard library, declared dependencies, or sibling files shown to you)".
# The script is a sibling of the test? No, it's in scripts/.
# Let's assume the test can import from scripts if we add the path.
# Or we can import the logic directly if we refactor, but we are extending, not re-authoring.
# We will import the main function and setup_directories from the script.
# To do this, we add the 'code' directory to sys.path.

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.setup_data_dirs import setup_directories, main, REQUIRED_DIRS

class TestDataDirectories:
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary directory to act as the project root."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup after test
        shutil.rmtree(temp_dir)

    def test_setup_directories_creates_structure(self, temp_project_root):
        """Test that setup_directories creates all required directories."""
        # Call the function
        created_dirs = setup_directories(temp_project_root)
        
        # Check that all required directories were created
        for dir_name in REQUIRED_DIRS:
            full_path = temp_project_root / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} is not a directory."
        
        # Check that the returned list contains the correct paths
        for expected_dir in REQUIRED_DIRS:
            assert str(temp_project_root / expected_dir) in created_dirs

    def test_setup_directories_idempotent(self, temp_project_root):
        """Test that running setup_directories multiple times does not raise errors."""
        # Run twice
        first_run = setup_directories(temp_project_root)
        second_run = setup_directories(temp_project_root)
        
        # Both should succeed and create the same directories
        assert len(first_run) == len(second_run)
        
        # Check that directories still exist
        for dir_name in REQUIRED_DIRS:
            full_path = temp_project_root / dir_name
            assert full_path.exists()

    def test_nested_directories_created(self, temp_project_root):
        """Test that nested directories (e.g., data/raw) are created with parents=True."""
        # The function should create data/raw even if data/ doesn't exist
        created_dirs = setup_directories(temp_project_root)
        
        # Check that data/raw exists
        raw_path = temp_project_root / "data" / "raw"
        assert raw_path.exists()
        
        # Check that data/derived exists
        derived_path = temp_project_root / "data" / "derived"
        assert derived_path.exists()
        
        # Check that data/gold_standard exists
        gold_path = temp_project_root / "data" / "gold_standard"
        assert gold_path.exists()
        
        # Check that artifacts/ exists
        artifacts_path = temp_project_root / "artifacts"
        assert artifacts_path.exists()
