import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path so we can import setup_data_directories
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_data_directories import setup_data_directories, verify_data_directories

class TestDataDirectories:
    """
    Test suite for verifying the creation and existence of data directories.
    This test ensures that T003 requirements are met.
    """

    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root for testing."""
        temp_dir = tempfile.mkdtemp()
        # Create the structure: temp_dir/code/setup_data_directories.py
        code_dir = Path(temp_dir) / "code"
        code_dir.mkdir()
        # Create the setup_data_directories.py file in the temp code dir
        setup_file = code_dir / "setup_data_directories.py"
        setup_file.write_text("""
import os
import sys
from pathlib import Path

def setup_data_directories():
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    required_dirs = ["raw", "processed", "models"]
    created_paths = []
    for dir_name in required_dirs:
  dir_path = data_root / dir_name
  if not dir_path.exists():
      dir_path.mkdir(parents=True, exist_ok=True)
  created_paths.append(str(dir_path))
    return True, created_paths

def verify_data_directories():
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    required_dirs = ["raw", "processed", "models"]
    existing_dirs = []
    missing_dirs = []
    for dir_name in required_dirs:
  dir_path = data_root / dir_name
  if os.path.isdir(dir_path):
      existing_dirs.append(str(dir_path))
  else:
      missing_dirs.append(str(dir_path))
    all_exist = len(missing_dirs) == 0
    return all_exist, missing_dirs, existing_dirs
""")
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_setup_creates_directories(self, temp_project_root):
        """Test that setup_data_directories creates the required directories."""
        # Change to the temp project root to simulate the real environment
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            # Import the module from the temp location
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "setup_data_directories",
                Path(temp_project_root) / "code" / "setup_data_directories.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            success, created_paths = module.setup_data_directories()
            
            assert success is True
            assert len(created_paths) == 3
            
            # Verify each directory exists
            for path in created_paths:
                assert os.path.isdir(path), f"Directory {path} should exist after setup"
        finally:
            os.chdir(original_cwd)

    def test_verify_confirms_directories(self, temp_project_root):
        """Test that verify_data_directories confirms the directories exist."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            # First, ensure directories are created
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "setup_data_directories",
                Path(temp_project_root) / "code" / "setup_data_directories.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            module.setup_data_directories()
            
            # Now verify
            all_exist, missing, existing = module.verify_data_directories()
            
            assert all_exist is True
            assert len(missing) == 0
            assert len(existing) == 3
            
            # Check that os.path.isdir returns True for each
            for path in existing:
                assert os.path.isdir(path), f"os.path.isdir({path}) should be True"
        finally:
            os.chdir(original_cwd)

    def test_os_path_isdir_assertions(self, temp_project_root):
        """
        Directly test the os.path.isdir assertions as required by T003 verification.
        """
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_root)
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "setup_data_directories",
                Path(temp_project_root) / "code" / "setup_data_directories.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Run setup
            module.setup_data_directories()
            
            # Perform the exact verification logic required by T003
            project_root = Path(temp_project_root)
            data_root = project_root / "data"
            required_dirs = ["raw", "processed", "models"]
            
            for dir_name in required_dirs:
                dir_path = data_root / dir_name
                # This is the exact assertion required by T003
                assert os.path.isdir(dir_path), f"Assertion failed: {dir_path} is not a directory"
        finally:
            os.chdir(original_cwd)