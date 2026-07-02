import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_project import create_structure

def test_create_structure_creates_directories():
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            created_dirs = create_structure()
            
            # Check that key directories exist
            assert os.path.exists("code")
            assert os.path.exists("data/raw")
            assert os.path.exists("data/processed")
            assert os.path.exists("tests")
            assert os.path.exists("outputs")
            
            # Check .gitkeep files
            assert os.path.exists("data/raw/.gitkeep")
            assert os.path.exists("data/processed/.gitkeep")
            
            # Check key files
            assert os.path.exists("README.md")
            assert os.path.exists("requirements.txt")
            assert os.path.exists("config/config.yaml")
        finally:
            os.chdir(original_cwd)