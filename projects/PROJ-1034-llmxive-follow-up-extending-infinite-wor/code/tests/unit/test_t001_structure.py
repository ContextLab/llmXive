import os
import pytest
from setup_project import REQUIRED_DIRS

class TestT001Structure:
    """
    Unit tests to verify the project directory structure required by T001.
    """

    @pytest.mark.parametrize("dir_path", REQUIRED_DIRS)
    def test_required_directory_exists(self, dir_path):
        """
        Verifies that each required directory exists on the filesystem.
        """
        assert os.path.isdir(dir_path), f"Required directory '{dir_path}' does not exist."

    def test_all_directories_created(self):
        """
        Verifies that the count of created directories matches the specification.
        """
        # We check if all specified paths are actually directories
        existing_count = sum(1 for d in REQUIRED_DIRS if os.path.isdir(d))
        assert existing_count == len(REQUIRED_DIRS), \
            f"Expected {len(REQUIRED_DIRS)} directories, found {existing_count}."

    def test_src_subdirectories_exist(self):
        """
        Verifies specific src subdirectories exist.
        """
        expected_src_dirs = [
            "src/sim",
            "src/analysis",
            "src/data",
            "src/cli",
            "src/tests"
        ]
        for d in expected_src_dirs:
            assert os.path.isdir(d), f"Missing src subdirectory: {d}"

    def test_data_subdirectories_exist(self):
        """
        Verifies specific data subdirectories exist.
        """
        expected_data_dirs = [
            "data/raw",
            "data/processed"
        ]
        for d in expected_data_dirs:
            assert os.path.isdir(d), f"Missing data subdirectory: {d}"