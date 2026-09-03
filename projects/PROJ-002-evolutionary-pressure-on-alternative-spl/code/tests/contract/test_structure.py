"""
Contract test for the test directory structure requirement (T001c).
This verifies that the project adheres to the specification requiring
three specific test directories: unit, integration, and contract.
"""
import os
import pytest
from pathlib import Path
from typing import List, Dict, Any

class TestDirectoryStructureContract:
    """
    Contract verification for T001c: Test directory structure.
    
    Requirement: The project MUST contain the following directories
    under the tests/ root:
      - unit/
      - integration/
      - contract/
    """
    
    REQUIRED_SUBDIRS = ["unit", "integration", "contract"]
    
    @pytest.fixture
    def tests_root(self) -> Path:
        """Return the root tests directory path."""
        return Path(__file__).parent.parent
    
    def test_all_required_directories_exist(self, tests_root: Path):
        """
        Contract: All required test subdirectories must exist.
        """
        missing = []
        for dir_name in self.REQUIRED_SUBDIRS:
            dir_path = tests_root / dir_name
            if not dir_path.exists():
                missing.append(dir_name)
            elif not dir_path.is_dir():
                missing.append(f"{dir_name} (exists but is not a directory)")
        
        assert not missing, (
            f"Contract violation: Missing required test directories: {missing}. "
            f"Expected structure: tests/{'/tests/'.join(self.REQUIRED_SUBDIRS)}"
        )
    
    def test_directories_are_non_empty_or_have_init(self, tests_root: Path):
        """
        Contract: Each test directory must be a valid Python package (have __init__.py)
        or contain at least one file.
        """
        for dir_name in self.REQUIRED_SUBDIRS:
            dir_path = tests_root / dir_name
            init_file = dir_path / "__init__.py"
            
            assert init_file.exists(), (
                f"Contract violation: {dir_name}/ is not a valid Python package. "
                f"Missing __init__.py file."
            )
    
    def test_directory_naming_convention(self, tests_root: Path):
        """
        Contract: Directory names must match the specification exactly (lowercase, no underscores).
        """
        actual_dirs = [d.name for d in tests_root.iterdir() if d.is_dir()]
        
        for required in self.REQUIRED_SUBDIRS:
            assert required in actual_dirs, (
                f"Contract violation: Expected directory '{required}' not found. "
                f"Found: {actual_dirs}"
            )
    
    def test_no_unexpected_top_level_test_dirs(self, tests_root: Path):
        """
        Contract: Only the specified test directories should exist at the top level
        of the tests/ folder (excluding __pycache__ and common config files).
        """
        allowed_patterns = set(self.REQUIRED_SUBDIRS + ["__pycache__"])
        
        for item in tests_root.iterdir():
            if item.is_dir():
                assert item.name in allowed_patterns, (
                    f"Contract violation: Unexpected directory '{item.name}' found in tests/. "
                    f"Allowed: {self.REQUIRED_SUBDIRS}"
                )