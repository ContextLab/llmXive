"""
Integration tests for state management workflow.
"""
import os
import tempfile
import pytest
import yaml
from pathlib import Path

from code.state_manager import (
    scan_raw_data_directory,
    generate_state_checksums,
    write_state_file,
    verify_state_checksums
)

def test_full_state_workflow(tmp_path):
    """
    Test the full workflow: create files, generate checksums, write state,
    modify file, and verify failure.
    """
    # Setup: Create a mock raw data directory
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    
    file1 = raw_dir / "file1.csv"
    file1.write_text("col1,col2\n1,2")
    
    file2 = raw_dir / "file2.csv"
    file2.write_text("col1,col2\n3,4")
    
    # Change to temp dir to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Act: Scan and generate
        files = scan_raw_data_directory(str(raw_dir))
        # Adjust paths to be relative to tmp_path for the test
        # In real usage, scan_raw_data_directory handles relative paths from cwd
        # Here we manually adjust for the test context
        
        # For this integration test, we use absolute paths in the logic
        # but verify the structure
        checksums = generate_state_checksums([str(file1), str(file2)])
        
        state_file = tmp_path / "state" / "data_checksums.yaml"
        write_state_file(checksums, str(state_file))
        
        # Assert: State file exists and has correct structure
        assert state_file.exists()
        with open(state_file) as f:
            state_data = yaml.safe_load(f)
        
        assert "raw_data_checksums" in state_data
        assert str(file1) in state_data["raw_data_checksums"]
        assert str(file2) in state_data["raw_data_checksums"]
        
        # Verify integrity
        assert verify_state_checksums(str(state_file)) is True
        
        # Tamper with a file
        file1.write_text("tampered")
        
        # Verify should fail
        assert verify_state_checksums(str(state_file)) is False
        
    finally:
        os.chdir(original_cwd)