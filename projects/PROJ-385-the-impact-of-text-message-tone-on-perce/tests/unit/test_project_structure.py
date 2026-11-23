import os
import pytest
from pathlib import Path
from config import (
    get_project_root, get_data_dir, get_raw_data_dir, get_processed_data_dir,
    get_consent_dir, get_specs_dir, get_contracts_dir, get_code_dir, get_tests_dir,
    get_figures_dir
)
from setup_project_structure import create_directories

class TestProjectStructure:
    """Tests to verify the project directory structure is correctly established."""

    def test_all_required_dirs_exist(self):
        """Verify that all standard directories exist after setup."""
        # Run setup to ensure creation
        create_directories()

        required_dirs = [
            get_code_dir(),
            get_tests_dir(),
            get_data_dir(),
            get_raw_data_dir(),
            get_processed_data_dir(),
            get_consent_dir(),
            get_specs_dir(),
            get_contracts_dir(),
            get_figures_dir(),
        ]

        for dir_path in required_dirs:
            assert dir_path.exists(), f"Directory {dir_path} does not exist."
            assert dir_path.is_dir(), f"Path {dir_path} is not a directory."
            assert os.access(dir_path, os.W_OK), f"Directory {dir_path} is not writable."

    def test_specs_subdirectory_exists(self):
        """Verify the specific specs subdirectory for this feature exists."""
        project_root = get_project_root()
        spec_dir = project_root / "specs" / "001-text-tone-emotional-support" / "contracts"
        
        # Ensure parent exists first
        spec_dir.parent.mkdir(parents=True, exist_ok=True)
        
        assert spec_dir.exists(), f"Spec contracts directory {spec_dir} does not exist."
        assert spec_dir.is_dir(), f"Path {spec_dir} is not a directory."