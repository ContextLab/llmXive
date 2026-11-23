"""
Unit tests for Task T001c directory creation.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path to import the verification logic
# Assuming tests are run from the project root or code/tests
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from verify_t001c_structure import verify_t001c_structure
from create_t001c_structure import create_t001c_structure

class TestT001cStructure:
    """Tests for the T001c directory structure creation."""

    @pytest.fixture
    def temp_code_dir(self):
        """Create a temporary directory to simulate the code/ directory."""
        temp_dir = tempfile.mkdtemp()
        # Create the basic structure that T001b would have created
        (Path(temp_dir) / "src").mkdir()
        (Path(temp_dir) / "tests").mkdir()
        (Path(temp_dir) / "data").mkdir()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_create_directories(self, temp_code_dir):
        """Test that create_t001c_structure creates all required directories."""
        create_t001c_structure(temp_code_dir)
        
        required_dirs = [
            "data/raw",
            "data/curated",
            "data/eval",
            "data/validation",
            "src/generation",
            "src/filtering",
            "src/training",
            "src/evaluation",
            "src/augmentation",
            "src/utils",
            "tests/unit",
            "tests/integration",
        ]
        
        for dir_name in required_dirs:
            full_path = temp_code_dir / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"

    def test_init_files_created(self, temp_code_dir):
        """Test that __init__.py files are created for Python packages."""
        create_t001c_structure(temp_code_dir)
        
        # Check a few key packages
        packages = [
            "src/generation",
            "src/filtering",
            "src/training",
            "tests/unit",
            "tests/integration"
        ]
        
        for pkg in packages:
            init_file = temp_code_dir / pkg / "__init__.py"
            assert init_file.exists(), f"__init__.py missing for {pkg}"

    def test_verify_function(self, temp_code_dir):
        """Test that the verification function returns True after creation."""
        create_t001c_structure(temp_code_dir)
        assert verify_t001c_structure(temp_code_dir) is True

    def test_verify_fails_with_missing_dirs(self, temp_code_dir):
        """Test that verification fails if directories are missing."""
        # Don't create directories, just verify
        assert verify_t001c_structure(temp_code_dir) is False

    def test_create_idempotent(self, temp_code_dir):
        """Test that running create_t001c_structure twice doesn't cause errors."""
        create_t001c_structure(temp_code_dir)
        # Should not raise an exception
        create_t001c_structure(temp_code_dir)
        
        # Verify structure still correct
        assert verify_t001c_structure(temp_code_dir) is True