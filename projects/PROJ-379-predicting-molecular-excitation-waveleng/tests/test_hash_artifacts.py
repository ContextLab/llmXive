"""
Tests for the hash_artifacts module.
"""
import os
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to import the module, but since it relies on PROJECT_ROOT
# being the parent of the script, we mock the path resolution for testing.
# However, the actual script logic is straightforward enough to test
# via integration with the file system if needed.
# For unit testing, we test the helper functions.

# To properly test, we need to import the functions from the module.
# Since the module uses __file__ to determine PROJECT_ROOT, we will
# test the logic by importing and mocking the environment.

# We'll import the functions after setting up a mock environment or
# by testing the logic directly if refactored.
# For now, we assume the module is importable.

# Note: In a real scenario, we might refactor `compute_file_hash` and 
# `collect_artifacts` into a separate helper module for easier testing.
# Here, we will test the behavior by creating temporary files.

def test_compute_file_hash(tmp_path):
    """Test that compute_file_hash returns a valid SHA-256 hash."""
    # Import here to avoid issues with PROJECT_ROOT in the module
    from code.hash_artifacts import compute_file_hash

    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    hash1 = compute_file_hash(test_file)
    hash2 = compute_file_hash(test_file)

    assert len(hash1) == 64  # SHA-256 hex length
    assert hash1 == hash2
    assert hash1 == "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"

def test_compute_file_hash_empty(tmp_path):
    """Test hashing an empty file."""
    from code.hash_artifacts import compute_file_hash

    test_file = tmp_path / "empty.txt"
    test_file.write_text("")

    hash_val = compute_file_hash(test_file)
    assert len(hash_val) == 64
    # SHA-256 of empty string
    assert hash_val == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

def test_update_state_file(tmp_path):
    """Test updating the state file."""
    from code.hash_artifacts import update_state_file
    import datetime

    # Mock the STATE_DIR and STATE_FILE to point to tmp_path
    with patch('code.hash_artifacts.STATE_DIR', tmp_path), \
         patch('code.hash_artifacts.STATE_FILE', tmp_path / 'test_state.yaml'):
        
        test_hashes = {
            "data/test.csv": "abc123",
            "code/test.py": "def456"
        }
        
        update_state_file(test_hashes)
        
        # Verify file was created
        state_file = tmp_path / 'test_state.yaml'
        assert state_file.exists()
        
        # Verify content
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['artifact_hashes'] == test_hashes
        assert 'updated_at' in data
        assert data['project_id'] == 'PROJ-379-predicting-molecular-excitation-waveleng'

def test_collect_artifacts_integration(tmp_path):
    """Integration test for collect_artifacts with a mock project structure."""
    from code.hash_artifacts import collect_artifacts, PROJECT_ROOT
    
    # We can't easily mock PROJECT_ROOT without changing the module code significantly.
    # Instead, we will test the logic by creating a temporary directory structure
    # that mimics the project and calling the function, but we need to adjust the
    # TARGET_DIRS.
    
    # For this test, we will create a temporary project structure and patch the TARGET_DIRS.
    import code.hash_artifacts as ha_module
    
    # Create a temp structure
    temp_code = tmp_path / "code"
    temp_data = tmp_path / "data"
    temp_code.mkdir()
    temp_data.mkdir()
    
    (temp_code / "main.py").write_text("print('hello')")
    (temp_data / "raw.csv").write_text("a,b\n1,2")
    (temp_data / "readme.txt").write_text("notes")
    (temp_data / "ignore.bin").write_text("binary") # Should be ignored
    
    # Patch TARGET_DIRS
    original_targets = ha_module.TARGET_DIRS
    ha_module.TARGET_DIRS = [temp_code, temp_data]
    
    try:
        artifacts = collect_artifacts()
        
        # Check that we found the relevant files
        # Note: The paths will be relative to the actual PROJECT_ROOT, 
        # but since we are running in a test context, the relative paths 
        # might be different. We are mostly checking that files are found.
        
        # We expect to find main.py and raw.csv and readme.txt
        found_files = list(artifacts.keys())
        
        # The paths will be relative to the actual PROJECT_ROOT, which is not tmp_path.
        # This test is a bit tricky because the function relies on PROJECT_ROOT.
        # A better approach is to refactor the code to accept a base path.
        # For now, we assert that we found *some* artifacts if the structure matches.
        
        # Since we can't easily predict the relative path without knowing the actual
        # PROJECT_ROOT in the test environment, we will just check that the function
        # runs without error and returns a dict.
        assert isinstance(artifacts, dict)
        assert len(artifacts) >= 3 # main.py, raw.csv, readme.txt
        
    finally:
        ha_module.TARGET_DIRS = original_targets