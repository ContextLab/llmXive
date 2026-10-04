import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup.create_specs_directories import create_directory, main

def test_create_directory_creates_new():
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = os.path.join(tmpdir, "new_test_dir")
        assert not os.path.exists(new_dir)
        create_directory(new_dir)
        assert os.path.exists(new_dir)
        assert os.path.isdir(new_dir)

def test_create_directory_exists_no_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        existing_dir = os.path.join(tmpdir, "existing_dir")
        os.makedirs(existing_dir)
        # Should not raise
        create_directory(existing_dir)
        assert os.path.exists(existing_dir)

def test_main_creates_specs_structure(monkeypatch, tmp_path):
    # Mock the current working directory to a temp location to avoid polluting the repo
    # However, the task specifically asks for 'specs/001-llmxive-followup' relative to root.
    # We will verify the function logic by checking if it attempts to create the path.
    # Since we cannot easily mock Path() globally without breaking other things,
    # we test the helper function primarily.
    
    # Verify that if we run main in a temp dir, it creates the structure there.
    # We temporarily change CWD for the test.
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        main()
        assert (tmp_path / "specs" / "001-llmxive-followup").exists()
        assert (tmp_path / "specs" / "001-llmxive-followup" / "contracts").exists()
    finally:
        os.chdir(original_cwd)
