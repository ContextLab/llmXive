import os
from pathlib import Path
import pytest

def test_data_directories_exist():
    """
    Contract test verifying that the required data directories exist.
    
    This test ensures that the project structure includes:
    - data/raw
    - data/processed
    - data/compliance
    """
    # Determine project root (parent of 'tests' directory)
    test_dir = Path(__file__).resolve().parent
    project_root = test_dir.parent
    
    # Define expected directories
    data_root = project_root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    compliance_dir = data_root / "compliance"
    
    # Assert existence of each directory
    assert data_root.exists(), f"Data root directory does not exist: {data_root}"
    assert data_root.is_dir(), f"Data root is not a directory: {data_root}"
    
    assert raw_dir.exists(), f"Raw data directory does not exist: {raw_dir}"
    assert raw_dir.is_dir(), f"Raw data path is not a directory: {raw_dir}"
    
    assert processed_dir.exists(), f"Processed data directory does not exist: {processed_dir}"
    assert processed_dir.is_dir(), f"Processed data path is not a directory: {processed_dir}"
    
    assert compliance_dir.exists(), f"Compliance data directory does not exist: {compliance_dir}"
    assert compliance_dir.is_dir(), f"Compliance data path is not a directory: {compliance_dir}"

def test_data_directories_writable():
    """
    Contract test verifying that data directories are writable.
    
    This ensures we can actually write files to these locations,
    not just that they exist.
    """
    test_dir = Path(__file__).resolve().parent
    project_root = test_dir.parent
    
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "compliance"
    ]
    
    for directory in data_dirs:
        # Try to create a temporary test file
        test_file = directory / ".write_test_marker"
        try:
            test_file.touch()
            test_file.unlink()  # Remove immediately after creation
            assert True, f"Directory {directory} is writable"
        except (IOError, OSError) as e:
            pytest.fail(f"Directory {directory} is not writable: {e}")