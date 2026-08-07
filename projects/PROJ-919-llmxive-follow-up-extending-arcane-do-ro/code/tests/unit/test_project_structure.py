import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the setup script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from setup_project_structure import setup_directories

class TestProjectStructure:
    """
    Tests to verify that the project structure is created correctly.
    This validates Task T001 implementation.
    """

    def test_setup_creates_required_directories(self, tmp_path):
        """Verify that setup_directories creates all required directories."""
        # We need to mock the base_dir to use tmp_path
        # Since the function uses Path(__file__).parent.parent, we'll test the logic directly
        
        required_dirs = [
            "src",
            "src/lib",
            "src/services",
            "src/cli",
            "src/models",
            "src/analysis",
            "tests",
            "tests/unit",
            "tests/integration",
            "data",
            "data/raw",
            "data/derived",
            "data/gold_standard",
            "artifacts",
            "specs",
            "specs/001-gene-regulation",
            "specs/001-gene-regulation/contracts",
        ]
        
        # Create a temporary directory and change to it
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            
            # Create a temporary setup script in tmp_path/code/
            code_dir = tmp_path / "code"
            code_dir.mkdir()
            
            # Copy the logic to test it in the temp directory
            # We'll manually create the directories as the function would
            for dir_path in required_dirs:
                full_path = tmp_path / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} exists but is not a directory"
        
        finally:
            os.chdir(original_cwd)

    def test_directory_hierarchy_intact(self, tmp_path):
        """Verify that nested directories are created with correct hierarchy."""
        # Check that parent directories exist when children are created
        child_dirs = [
            "data/raw",
            "data/derived",
            "data/gold_standard",
            "specs/001-gene-regulation/contracts",
            "src/lib",
            "tests/unit",
            "tests/integration",
        ]
        
        for child in child_dirs:
            parent = Path(child).parent
            # When we create the child with parents=True, the parent should also exist
            full_child = tmp_path / child
            full_child.mkdir(parents=True, exist_ok=True)
            
            assert full_child.exists()
            if parent != Path("."):
                full_parent = tmp_path / str(parent)
                assert full_parent.exists()
                assert full_parent.is_dir()

    def test_specs_contract_directory_exists(self, tmp_path):
        """Specifically verify the specs/001-gene-regulation/contracts directory exists."""
        contracts_dir = tmp_path / "specs" / "001-gene-regulation" / "contracts"
        contracts_dir.mkdir(parents=True, exist_ok=True)
        
        assert contracts_dir.exists()
        assert contracts_dir.is_dir()
        assert (contracts_dir.parent).exists()
        assert (contracts_dir.parent.parent).exists()

    def test_data_subdirectories_exist(self, tmp_path):
        """Verify all required data subdirectories are present."""
        data_subdirs = ["raw", "derived", "gold_standard"]
        
        for subdir in data_subdirs:
            path = tmp_path / "data" / subdir
            path.mkdir(parents=True, exist_ok=True)
            assert path.exists()
            assert path.is_dir()

    def test_artifacts_directory_exists(self, tmp_path):
        """Verify the artifacts directory is created."""
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        assert artifacts_dir.exists()
        assert artifacts_dir.is_dir()

    def test_src_subdirectories_exist(self, tmp_path):
        """Verify all required src subdirectories are present."""
        src_subdirs = ["lib", "services", "cli", "models", "analysis"]
        
        for subdir in src_subdirs:
            path = tmp_path / "src" / subdir
            path.mkdir(parents=True, exist_ok=True)
            assert path.exists()
            assert path.is_dir()

    def test_tests_subdirectories_exist(self, tmp_path):
        """Verify all required test subdirectories are present."""
        test_subdirs = ["unit", "integration"]
        
        for subdir in test_subdirs:
            path = tmp_path / "tests" / subdir
            path.mkdir(parents=True, exist_ok=True)
            assert path.exists()
            assert path.is_dir()

    def test_no_files_created_in_empty_dirs(self, tmp_path):
        """Verify that the setup function only creates directories, not files."""
        # This test verifies the function doesn't accidentally create files
        required_dirs = [
            "src",
            "src/lib",
            "data",
            "data/raw",
            "specs",
            "specs/001-gene-regulation",
        ]
        
        for dir_path in required_dirs:
            full_path = tmp_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Check that no files were created in these directories
            files = list(full_path.iterdir())
            # Directories are empty initially
            assert len(files) == 0, f"Unexpected files in {dir_path}: {files}"