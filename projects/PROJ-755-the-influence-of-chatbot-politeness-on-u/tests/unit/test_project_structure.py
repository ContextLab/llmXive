import os
import sys
from pathlib import Path
import tempfile
import pytest

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_structure

class TestProjectStructure:
    """Tests for the project structure creation functionality."""

    def test_creates_all_required_directories(self):
        """Verify that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            result = create_structure(base_path)
            
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "code/utils",
                "tests",
                "tests/contract",
                "tests/unit",
                "tests/integration",
                "docs",
                "state"
            ]
            
            for dir_path in required_dirs:
                full_path = base_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} was not created"
                assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_creates_gitkeep_in_data_directories(self):
        """Verify that .gitkeep files are created in data directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            result = create_structure(base_path)
            
            for data_dir in ["data/raw", "data/processed"]:
                gitkeep_path = base_path / data_dir / ".gitkeep"
                assert gitkeep_path.exists(), f".gitkeep not created in {data_dir}"
                assert gitkeep_path.is_file(), f".gitkeep in {data_dir} is not a file"

    def test_creates_gitignore_file(self):
        """Verify that .gitignore file is created with correct content."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            result = create_structure(base_path)
            
            gitignore_path = base_path / ".gitignore"
            assert gitignore_path.exists(), ".gitignore file was not created"
            
            with open(gitignore_path, 'r') as f:
                content = f.read()
            
            # Check for required patterns
            assert "data/raw/*" in content, ".gitignore missing 'data/raw/*'"
            assert "data/processed/*" in content, ".gitignore missing 'data/processed/*'"
            assert "__pycache__" in content, ".gitignore missing '__pycache__'"
            assert "data/models/*" in content, ".gitignore missing 'data/models/*'"

    def test_creates_gitkeep_in_root_code_and_tests(self):
        """Verify that .gitkeep files are created in root code and tests directories."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            result = create_structure(base_path)
            
            code_gitkeep = base_path / "code" / ".gitkeep"
            tests_gitkeep = base_path / "tests" / ".gitkeep"
            
            assert code_gitkeep.exists(), "code/.gitkeep was not created"
            assert tests_gitkeep.exists(), "tests/.gitkeep was not created"

    def test_no_errors_on_successful_creation(self):
        """Verify that no errors are reported on successful creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            result = create_structure(base_path)
            
            assert len(result["errors"]) == 0, f"Errors reported: {result['errors']}"
            assert len(result["created_dirs"]) > 0, "No directories were created"
            assert len(result["created_files"]) > 0, "No files were created"

    def test_idempotent_creation(self):
        """Verify that running create_structure twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_path = Path(tmp_dir)
            
            # First run
            result1 = create_structure(base_path)
            assert len(result1["errors"]) == 0, "First run had errors"
            
            # Second run
            result2 = create_structure(base_path)
            assert len(result2["errors"]) == 0, "Second run had errors"
            
            # Verify structure still exists
            required_dirs = [
                "data/raw",
                "data/processed",
                "code",
                "code/utils",
                "tests",
                "tests/contract",
                "tests/unit",
                "tests/integration",
                "docs",
                "state"
            ]
            
            for dir_path in required_dirs:
                full_path = base_path / dir_path
                assert full_path.exists(), f"Directory {dir_path} missing after second run"