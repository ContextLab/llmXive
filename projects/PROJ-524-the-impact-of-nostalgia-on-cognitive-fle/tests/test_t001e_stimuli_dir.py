"""
Test for Task T001e: Stimuli Directory Creation.

Verifies that the `data/stimuli/` directory exists after running the task.
"""
import os
import pytest
from pathlib import Path
from code.task_t001e_create_stimuli_dir import create_stimuli_directory

def test_stimuli_directory_creation():
    """
    Test that the stimuli directory is created successfully.
    """
    # Execute the creation function
    result = create_stimuli_directory()

    # Assert the function returned success
    assert result is True, "create_stimuli_directory should return True on success"

    # Verify the directory actually exists on disk
    stimuli_path = Path("data/stimuli")
    assert stimuli_path.exists(), f"Directory {stimuli_path} does not exist"
    assert stimuli_path.is_dir(), f"{stimuli_path} exists but is not a directory"

def test_stimuli_directory_is_writable():
    """
    Test that the stimuli directory is writable (can create a temp file).
    """
    stimuli_path = Path("data/stimuli")
    
    if not stimuli_path.exists():
        pytest.skip("Stimuli directory does not exist, skipping writability test")

    test_file = stimuli_path / ".write_test_marker"
    try:
        # Try to create a file
        with open(test_file, 'w') as f:
            f.write("test")
        
        # Verify it exists
        assert test_file.exists(), "Test file was not created"
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
