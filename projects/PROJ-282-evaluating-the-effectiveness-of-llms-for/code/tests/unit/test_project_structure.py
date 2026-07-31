import os
import pytest
from pathlib import Path
import tempfile
import shutil
from setup_project_structure import create_structure

class TestProjectStructure:
    """Tests for the project structure creation task T001."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory to simulate the project root."""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        yield Path(temp_dir)
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)

    def test_directory_structure_exists(self, temp_project_dir):
        """Verify that create_structure() creates all required directories."""
        # Run the structure creation
        result = create_structure()
        assert result is True

        required_dirs = [
            "src",
            "tests",
            "data",
            "data/raw",
            "data/processed",
            "data/results",
            "state",
            "contracts",
            "figures",
            "data/logs"
        ]

        for dir_name in required_dirs:
            full_path = temp_project_dir / dir_name
            assert full_path.exists(), f"Directory {dir_name} was not created"
            assert full_path.is_dir(), f"{dir_name} exists but is not a directory"

    def test_init_files_created(self, temp_project_dir):
        """Verify that __init__.py files are created for Python packages."""
        create_structure()

        package_dirs = ["src", "tests"]
        for dir_name in package_dirs:
            full_path = temp_project_dir / dir_name
            init_file = full_path / "__init__.py"
            assert init_file.exists(), f"__init__.py missing in {dir_name}"

    def test_gitkeep_files_created(self, temp_project_dir):
        """Verify that .gitkeep files are created in empty data directories."""
        create_structure()

        data_dirs = ["data/raw", "data/processed", "data/results", "data/logs"]
        for dir_name in data_dirs:
            full_path = temp_project_dir / dir_name
            keep_file = full_path / ".gitkeep"
            assert keep_file.exists(), f".gitkeep missing in {dir_name}"
