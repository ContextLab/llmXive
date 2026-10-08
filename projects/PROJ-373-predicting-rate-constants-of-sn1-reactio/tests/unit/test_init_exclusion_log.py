import os
import csv
import pytest
from pathlib import Path
from code.data.init_exclusion_log import initialize_exclusion_log

def test_init_exclusion_log_creates_file_with_header(tmp_path):
    """
    Test that initialize_exclusion_log creates a file with the correct header.
    """
    # Change to tmp_path to avoid writing to real data directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Ensure data/processed directory exists
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        # Run the initialization
        success = initialize_exclusion_log()
        
        # Verify the function returned True
        assert success is True, "initialize_exclusion_log should return True on success"
        
        # Verify the file exists
        output_path = Path("data/processed/exclusion_raw.log")
        assert output_path.exists(), "Exclusion log file should be created"
        
        # Verify the file has the correct header
        with open(output_path, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['row_index', 'reason', 'original_smiles'], \
                f"Header should be ['row_index', 'reason', 'original_smiles'], got {header}"
        
        # Verify the file has only the header (no data rows)
        with open(output_path, 'r', newline='') as f:
            lines = f.readlines()
            assert len(lines) == 1, "File should contain only the header row"
    
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_init_exclusion_log_overwrites_existing_file(tmp_path):
    """
    Test that initialize_exclusion_log overwrites an existing file.
    """
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Ensure data/processed directory exists
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        # Create a pre-existing file with different content
        output_path = Path("data/processed/exclusion_raw.log")
        with open(output_path, 'w') as f:
            f.write("old_content\n")
        
        # Run the initialization
        success = initialize_exclusion_log()
        
        # Verify the function returned True
        assert success is True, "initialize_exclusion_log should return True on success"
        
        # Verify the file content was overwritten
        with open(output_path, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['row_index', 'reason', 'original_smiles'], \
                f"Header should be ['row_index', 'reason', 'original_smiles'], got {header}"
        
        # Verify the file has only the header
        with open(output_path, 'r', newline='') as f:
            lines = f.readlines()
            assert len(lines) == 1, "File should contain only the header row after overwrite"
    
    finally:
        os.chdir(original_cwd)