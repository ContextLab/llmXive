"""
Tests for T007: State Update Module

Verifies that SHA-256 hashes are computed correctly and the state file
is updated as expected.
"""
import os
import sys
import tempfile
import shutil
import hashlib
import yaml
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent / "code"
sys.path.insert(0, str(code_dir))

from utils.error_contract import calculate_checksum
import importlib.util

# Dynamically load the module to avoid import conflicts if needed, 
# but standard import should work if structure is correct.
spec = importlib.util.spec_from_file_location("update_state", code_dir / "04_update_state.py")
update_state_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update_state_module)

# We need to mock the global variables in the module to point to our temp dirs
# because the module defines them at import time based on __file__.

def test_calculate_sha256():
    """Test that SHA-256 calculation matches standard library."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = b"Hello, World! This is a test for hashing."
        tmp.write(content)
        tmp_path = Path(tmp.name)
    
    try:
        # Calculate using our function
        computed_hash = update_state_module.calculate_sha256(tmp_path)
        
        # Calculate using standard hashlib for verification
        expected_hash = hashlib.sha256(content).hexdigest()
        
        assert computed_hash == expected_hash, f"Hash mismatch: {computed_hash} != {expected_hash}"
    finally:
        tmp_path.unlink()

def test_scan_directory_for_artifacts():
    """Test that the scanner finds files and computes hashes."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create nested structure
        sub_dir = tmp_path / "subdir"
        sub_dir.mkdir()
        
        file1 = tmp_path / "file1.txt"
        file1.write_text("Content 1")
        
        file2 = sub_dir / "file2.txt"
        file2.write_text("Content 2")
        
        # Create a hidden file that should be skipped
        hidden = tmp_path / ".hidden"
        hidden.write_text("Hidden content")
        
        # Mock the PROJECT_ROOT and directory to scan
        original_project_root = update_state_module.PROJECT_ROOT
        update_state_module.PROJECT_ROOT = tmp_path
        
        try:
            artifacts = update_state_module.scan_directory_for_artifacts(tmp_path)
            
            # Check counts
            assert len(artifacts) == 2, f"Expected 2 files, found {len(artifacts)}"
            
            # Check relative paths
            paths = [a["path"] for a in artifacts]
            assert "file1.txt" in paths
            assert "subdir/file2.txt" in paths
            assert ".hidden" not in paths
            
            # Check hashes
            for artifact in artifacts:
                assert "sha256" in artifact
                assert "size_bytes" in artifact
                assert artifact["size_bytes"] > 0
        finally:
            update_state_module.PROJECT_ROOT = original_project_root

def test_load_and_update_state():
    """Test loading and updating the state YAML."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        state_file = tmp_path / "test_state.yaml"
        
        # Mock the STATE_FILE_PATH
        original_state_file = update_state_module.STATE_FILE_PATH
        update_state_module.STATE_FILE_PATH = state_file
        
        try:
            # Test loading non-existent file
            state = update_state_module.load_current_state()
            assert state == {}
            
            # Test updating state
            test_data = {
                "project_id": "TEST-001",
                "artifacts": {
                    "data": {
                        "count": 1,
                        "files": [{"path": "test.txt", "sha256": "abc123"}]
                    }
                }
            }
            
            update_state_module.update_state_file(test_data)
            
            # Verify file exists and content matches
            assert state_file.exists()
            with open(state_file, "r") as f:
                loaded_data = yaml.safe_load(f)
                
            assert loaded_data["project_id"] == "TEST-001"
            assert loaded_data["artifacts"]["data"]["count"] == 1
            
        finally:
            update_state_module.STATE_FILE_PATH = original_state_file

def test_main_function():
    """Test the main entry point with a mock directory structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create mock data and results directories
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "test_data.csv").write_text("col1,col2\n1,2")
        
        results_dir = tmp_path / "results"
        results_dir.mkdir()
        (results_dir / "report.md").write_text("# Report")
        
        state_dir = tmp_path / "state" / "projects"
        state_dir.mkdir(parents=True)
        
        # Mock globals
        original_root = update_state_module.PROJECT_ROOT
        original_data = update_state_module.DATA_DIR
        original_results = update_state_module.RESULTS_DIR
        original_state_dir = update_state_module.STATE_DIR
        original_state_file = update_state_module.STATE_FILE_PATH
        original_state_name = update_state_module.STATE_FILE_NAME
        
        update_state_module.PROJECT_ROOT = tmp_path
        update_state_module.DATA_DIR = data_dir
        update_state_module.RESULTS_DIR = results_dir
        update_state_module.STATE_DIR = state_dir
        update_state_module.STATE_FILE_NAME = "test_project.yaml"
        update_state_module.STATE_FILE_PATH = state_dir / "test_project.yaml"
        
        try:
            exit_code = update_state_module.main()
            assert exit_code == 0, "Main function should return 0 on success"
            
            # Verify state file was created
            assert update_state_module.STATE_FILE_PATH.exists()
            
            # Verify content
            with open(update_state_module.STATE_FILE_PATH, "r") as f:
                state = yaml.safe_load(f)
                
            assert "artifacts" in state
            assert "data" in state["artifacts"]
            assert "results" in state["artifacts"]
            assert state["artifacts"]["data"]["count"] == 1
            assert state["artifacts"]["results"]["count"] == 1
            
        finally:
            # Restore globals
            update_state_module.PROJECT_ROOT = original_root
            update_state_module.DATA_DIR = original_data
            update_state_module.RESULTS_DIR = original_results
            update_state_module.STATE_DIR = original_state_dir
            update_state_module.STATE_FILE_NAME = original_state_name
            update_state_module.STATE_FILE_PATH = original_state_file