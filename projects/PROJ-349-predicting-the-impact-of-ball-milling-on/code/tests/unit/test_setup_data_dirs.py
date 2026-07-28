import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from code.setup_data_dirs import setup_directories

class TestSetupDataDirs:
    def test_setup_directories_creates_all_folders(self, tmp_path):
        """Verify that setup_directories creates all required directories."""
        with patch('code.setup_data_dirs.Path.cwd', return_value=tmp_path):
            setup_directories()

        required_dirs = [
            "src",
            "tests",
            "data/raw",
            "data/processed",
            "data/splits",
            "results",
            "contracts",
            ".github/workflows"
        ]

        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"

    def test_setup_directories_idempotent(self, tmp_path):
        """Verify that running setup_directories twice doesn't fail."""
        with patch('code.setup_data_dirs.Path.cwd', return_value=tmp_path):
            # First run
            setup_directories()
            # Second run
            setup_directories()
        
        # Verify existence again
        assert (tmp_path / "src").exists()
        assert (tmp_path / "data/raw").exists()