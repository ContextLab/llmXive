import os
import tempfile
from pathlib import Path
import pytest

# Import the function we are testing
from setup_directories import setup_code_directories

def test_setup_directories_creates_state_and_docs():
    """Test that setup_code_directories creates state/ and docs/ directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Run the setup function
        setup_code_directories(tmp_dir)
        
        base_path = Path(tmp_dir)
        
        # Verify state directory exists
        state_path = base_path / "state"
        assert state_path.exists(), "state/ directory should be created"
        assert state_path.is_dir(), "state/ should be a directory"
        
        # Verify docs directory exists
        docs_path = base_path / "docs"
        assert docs_path.exists(), "docs/ directory should be created"
        assert docs_path.is_dir(), "docs/ should be a directory"

def test_setup_directories_creates_existing_dirs():
    """Test that existing directories from T002/T003 are still created."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        setup_code_directories(tmp_dir)
        
        base_path = Path(tmp_dir)
        
        # Check a few key directories from previous tasks
        expected_dirs = [
            "code",
            "code/data",
            "data/raw",
            "data/processed",
        ]
        
        for dir_name in expected_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"{dir_name}/ should be created"
            assert dir_path.is_dir(), f"{dir_name}/ should be a directory"