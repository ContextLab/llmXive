"""
Unit tests for project structure verification (Task T006a).

These tests verify that the required directory structure and files
exist as specified in the project setup.
"""
import pytest
from pathlib import Path
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.verify_structure import (
    REQUIRED_DIRS,
    REQUIRED_FILES,
    check_structure,
    print_tree_structure,
)


class TestProjectStructure:
    """Test cases for project structure verification."""

    def test_required_dirs_exist(self):
        """Verify all required directories exist."""
        for d in REQUIRED_DIRS:
            p = Path(d)
            assert p.is_dir(), f"Directory {d} does not exist"

    def test_required_files_exist(self):
        """Verify all required __init__.py files exist."""
        for f in REQUIRED_FILES:
            p = Path(f)
            assert p.is_file(), f"File {f} does not exist"

    def test_check_structure_returns_true_on_success(self):
        """Test that check_structure returns True when all items exist."""
        success, missing = check_structure()
        # If this test runs, the structure should be correct
        assert success, f"Structure check failed. Missing: {missing}"

    def test_empty_missing_list_on_success(self):
        """Test that missing list is empty when structure is correct."""
        success, missing = check_structure()
        assert success
        assert len(missing) == 0, f"Expected no missing items, got: {missing}"

    def test_specific_directories(self):
        """Test specific critical directories exist."""
        critical_dirs = [
            "code/data_generation",
            "code/training",
            "code/evaluation",
            "data/raw",
            "data/processed",
            "tests/unit",
            "specs/001-predict-stiffness-cnn/contracts",
        ]
        for d in critical_dirs:
            assert Path(d).is_dir(), f"Critical directory {d} missing"

    def test_specific_init_files(self):
        """Test specific critical __init__.py files exist."""
        critical_inits = [
            "code/__init__.py",
            "code/data_generation/__init__.py",
            "code/training/__init__.py",
            "tests/__init__.py",
        ]
        for f in critical_inits:
            assert Path(f).is_file(), f"Critical init file {f} missing"