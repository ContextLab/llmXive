"""
Integration test for Task T001: Project Directory Structure.
Verifies that the required directory tree exists after running setup_project_structure.py.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure we can import from the code directory if tests are run from root
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
code_dir = root_dir / "code"

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project_structure import REQUIRED_DIRS

class TestDirectoryStructure:
    """Tests to verify the existence of required directories for T001."""

    @pytest.fixture
    def base_path(self):
        """Fixture to get the current working directory (project root)."""
        return Path.cwd()

    @pytest.mark.parametrize("dir_path_str", REQUIRED_DIRS)
    def test_directory_exists(self, base_path, dir_path_str):
        """
        Asserts that every directory defined in REQUIRED_DIRS exists.
        This directly satisfies the T001 requirement to verify existence.
        """
        full_path = base_path / dir_path_str
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

    def test_data_subdirectories(self, base_path):
        """Verifies specific data subdirectories mentioned in T001."""
        data_dirs = ["data/raw", "data/processed", "data/outputs"]
        for d in data_dirs:
            assert (base_path / d).exists(), f"Missing data subdirectory: {d}"

    def test_code_subdirectories(self, base_path):
        """Verifies specific code subdirectories mentioned in T001."""
        code_dirs = [
            "code/ingestion", "code/features", "code/models",
            "code/evaluation", "code/visualization", "code/utils"
        ]
        for d in code_dirs:
            assert (base_path / d).exists(), f"Missing code subdirectory: {d}"

    def test_tests_subdirectories(self, base_path):
        """Verifies specific test subdirectories mentioned in T001."""
        test_dirs = ["tests/contract", "tests/integration"]
        for d in test_dirs:
            assert (base_path / d).exists(), f"Missing test subdirectory: {d}"
