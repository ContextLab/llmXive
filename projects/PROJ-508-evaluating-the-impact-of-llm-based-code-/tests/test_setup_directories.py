import os
import pytest
from pathlib import Path
import sys

# Add parent of tests to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_directories import create_directories

def test_t010_docs_output_directory_exists():
    """
    Test for T010: Verify that the directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/docs/output/` exists.
    This test runs create_directories() to ensure the structure is established,
    then asserts the specific T010 path exists on disk.
    """
    # Ensure the directories are created
    created = create_directories()
    
    # Determine the expected path relative to the test file location
    # Assuming project structure: code/setup_directories.py and tests/
    project_root = Path(__file__).resolve().parent.parent
    t010_path = project_root / "docs" / "output"
    
    # Assert the directory exists
    assert t010_path.exists(), f"Directory missing: {t010_path}"
    assert t010_path.is_dir(), f"Path exists but is not a directory: {t010_path}"
    
    # Optional: Verify it is empty or contains expected placeholder if we added one
    # For T010, existence is the primary requirement.
