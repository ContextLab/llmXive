import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from create_project_structure import create_project_structure

class TestProjectStructureIntegration:
    """
    Integration test for task T001.
    Verifies that the project structure is created correctly and can be used
    by other modules in the pipeline.
    """

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for integration test."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)
        
        yield
        
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_project_structure_creation(self):
        """
        Integration test: Create the full project structure and verify
        that all expected directories and files exist.
        """
        # Create the structure
        result = create_project_structure()
        
        # Verify base path
        base_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
        assert base_path.exists()
        
        # Verify all required directories
        expected_dirs = {
            "src",
            "tests",
            "data",
            "src/generation",
            "src/filtering",
            "src/training",
            "src/evaluation",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "data/raw",
            "data/curated",
            "data/eval",
            "data/validation",
        }
        
        for dir_name in expected_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} missing"
            assert dir_path.is_dir(), f"Path {dir_path} is not a directory"
        
        # Verify __init__.py files for Python packages
        expected_init_files = {
            "src/__init__.py",
            "tests/__init__.py",
            "src/generation/__init__.py",
            "src/filtering/__init__.py",
            "src/training/__init__.py",
            "src/evaluation/__init__.py",
            "src/utils/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py",
        }
        
        for init_file in expected_init_files:
            file_path = base_path / init_file
            assert file_path.exists(), f"__init__.py file {file_path} missing"
            assert file_path.is_file(), f"Path {file_path} is not a file"

    def test_structure_compatibility_with_imports(self):
        """
        Integration test: Verify that the created structure supports
        importing from sibling modules as defined in the API surface.
        """
        result = create_project_structure()
        
        # Verify that we can import from the created structure
        # This tests that the __init__.py files are in place
        try:
            # These imports should work if the structure is correct
            from src.utils.io_utils import ensure_dirs
            from src.utils.logging import get_logger
            from src.training.config import TrainingConfig
            from src.generation.prompts import PromptManager
            from src.filtering.pybullet_filter import CanonicalSimulation
            from src.filtering.cv_pipeline import TrajectoryExtractor
            from src.filtering.prompt_to_scene import parse_prompt_for_objects
            
            # If we get here, the imports succeeded
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import from created structure: {e}")

    def test_data_directory_permissions(self):
        """
        Integration test: Verify that data directories are writable.
        """
        result = create_project_structure()
        
        base_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
        data_dirs = [
            "data/raw",
            "data/curated",
            "data/eval",
            "data/validation",
        ]
        
        for dir_name in data_dirs:
            dir_path = base_path / dir_name
            test_file = dir_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except (OSError, IOError) as e:
                pytest.fail(f"Cannot write to {dir_path}: {e}")

    def test_structure_size_and_completeness(self):
        """
        Integration test: Verify the total number of directories and files
        matches expectations for a complete project setup.
        """
        result = create_project_structure()
        
        # We expect 14 directories and 9 __init__.py files based on the task spec
        assert len(result["directories"]) == 14, \
            f"Expected 14 directories, got {len(result['directories'])}"
        assert len(result["init_files"]) == 9, \
            f"Expected 9 __init__.py files, got {len(result['init_files'])}"
        
        # Verify all directories are under the base path
        base_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
        for dir_path in result["directories"]:
            dir_path_obj = Path(dir_path)
            assert dir_path_obj.is_relative_to(base_path), \
                f"Directory {dir_path} is not under base path {base_path}"
        
        # Verify all init files are under the base path
        for init_path in result["init_files"]:
            init_path_obj = Path(init_path)
            assert init_path_obj.is_relative_to(base_path), \
                f"Init file {init_path} is not under base path {base_path}"
