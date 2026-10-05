"""
Unit tests for setup_directories.py (T001).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code directory to path for import
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_directories import setup_directories

def test_setup_directories_creates_structure():
    """
    Test that setup_directories creates the expected directory structure.
    Since setup_directories uses Path.cwd(), we change to a temp directory.
    """
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try:
            # Call the setup function
            setup_directories()

            # Verify directories exist
            project_root = Path(tmpdir) / "projects" / "PROJ-915-llmxive-follow-up-extending-measuring-ep"
            
            expected_dirs = [
                "code",
                "data/raw",
                "data/processed",
                "data/interim",
                "data/results",
                "state",
                "tests/unit",
                "tests/integration",
                "docs"
            ]

            for dir_name in expected_dirs:
                full_path = project_root / dir_name
                assert full_path.exists(), f"Directory {full_path} was not created"
                assert full_path.is_dir(), f"{full_path} is not a directory"
        finally:
            os.chdir(original_cwd)