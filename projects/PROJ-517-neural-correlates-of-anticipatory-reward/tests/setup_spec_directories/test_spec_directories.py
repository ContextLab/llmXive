import os
import pytest
from pathlib import Path
import sys

# Add parent to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_spec_directories import create_spec_directories

def test_spec_directory_created():
    """
    Test that T001c successfully creates the required spec directory.
    """
    # Get the project root relative to this test file
    # Assuming test structure: tests/setup_spec_directories/test_*.py
    # Project root is two levels up
    project_root = Path(__file__).resolve().parent.parent.parent
    expected_dir = project_root / "specs" / "001-neural-correlates-of-anticipatory-reward"

    # Run the function
    result = create_spec_directories()

    # Assertions
    assert result is True, "create_spec_directories should return True on success"
    assert expected_dir.exists(), f"Directory {expected_dir} should exist after creation"
    assert expected_dir.is_dir(), f"{expected_dir} should be a directory"

def test_spec_directory_structure():
    """
    Verify the directory was created with correct nesting.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    specs_base = project_root / "specs"
    feature_dir = specs_base / "001-neural-correlates-of-anticipatory-reward"

    # Ensure parent exists
    assert specs_base.exists(), "specs/ base directory should exist"
    assert feature_dir.exists(), "Feature specific directory should exist"