import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup_project import create_structure
from config import get_project_root

class TestSetupStructure:
    """Tests for project structure creation (T001b)."""

    def test_create_structure_creates_all_directories(self, tmp_path):
        """Verify that create_structure creates all required directories."""
        # Mock get_project_root to return tmp_path
        with patch('setup_project.get_project_root', return_value=tmp_path):
            created = create_structure()
        
        # Verify all directories were created
        assert len(created) == 7, f"Expected 7 directories, got {len(created)}"
        
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/tests",
            "code/utils",
            "code/models",
            "docs"
        ]
        
        for dir_path in required_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} exists but is not a directory"

    def test_structure_uses_sibling_directories(self, tmp_path):
        """Verify that data/ and code/ are siblings, not nested."""
        with patch('setup_project.get_project_root', return_value=tmp_path):
            create_structure()
        
        # Verify data/ and code/ are at the same level
        data_dir = tmp_path / "data"
        code_dir = tmp_path / "code"
        
        assert data_dir.exists(), "data/ directory should exist"
        assert code_dir.exists(), "code/ directory should exist"
        
        # Verify they are siblings (both direct children of project root)
        assert data_dir.parent == code_dir.parent, "data/ and code/ should be siblings"
        
        # Verify they are not nested
        assert not (data_dir / "code").exists(), "code/ should not be inside data/"
        assert not (code_dir / "data").exists(), "data/ should not be inside code/"

    def test_nested_directories_exist(self, tmp_path):
        """Verify that nested directories like data/raw and code/tests exist."""
        with patch('setup_project.get_project_root', return_value=tmp_path):
            create_structure()
        
        # Check nested structure
        assert (tmp_path / "data" / "raw").exists(), "data/raw should exist"
        assert (tmp_path / "data" / "processed").exists(), "data/processed should exist"
        assert (tmp_path / "code" / "tests").exists(), "code/tests should exist"
        assert (tmp_path / "code" / "utils").exists(), "code/utils should exist"
        assert (tmp_path / "code" / "models").exists(), "code/models should exist"

    def test_create_structure_idempotent(self, tmp_path):
        """Verify that running create_structure multiple times doesn't fail."""
        with patch('setup_project.get_project_root', return_value=tmp_path):
            # Run twice
            result1 = create_structure()
            result2 = create_structure()
        
        # Both runs should succeed and return the same number of directories
        assert len(result1) == len(result2) == 7
        
        # All directories should still exist
        required_dirs = [
            "data/raw",
            "data/processed",
            "code",
            "code/tests",
            "code/utils",
            "code/models",
            "docs"
        ]
        
        for dir_path in required_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists()