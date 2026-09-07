"""
Test suite to verify directory structure creation.
Specifically tests T002: code/, code/utils/, code/models/
"""
import os
from pathlib import Path
import pytest


class TestDirectoryStructure:
    """Tests for the directory structure setup (T002)."""

    @pytest.fixture(autouse=True)
    def setup_dirs(self):
        """Ensure directories exist before running tests."""
        from code.setup_directories import main
        main()

    def test_code_directory_exists(self):
        """Verify code/ directory exists."""
        code_dir = Path("code")
        assert code_dir.exists(), "code/ directory must exist"
        assert code_dir.is_dir(), "code/ must be a directory"

    def test_code_utils_directory_exists(self):
        """Verify code/utils/ directory exists."""
        utils_dir = Path("code/utils")
        assert utils_dir.exists(), "code/utils/ directory must exist"
        assert utils_dir.is_dir(), "code/utils/ must be a directory"

    def test_code_models_directory_exists(self):
        """Verify code/models/ directory exists."""
        models_dir = Path("code/models")
        assert models_dir.exists(), "code/models/ directory must exist"
        assert models_dir.is_dir(), "code/models/ must be a directory"

    def test_directory_structure_integrity(self):
        """Verify the parent-child relationship of directories."""
        code_dir = Path("code")
        utils_dir = Path("code/utils")
        models_dir = Path("code/models")

        # Verify utils is inside code
        assert utils_dir.parent == code_dir, "code/utils/ must be inside code/"
        
        # Verify models is inside code
        assert models_dir.parent == code_dir, "code/models/ must be inside code/"