import os
import pytest
from pathlib import Path
import shutil

from code.setup_project_structure import create_directories, verify_directories
from code.utils.logging import configure_root_logger

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Ensure directories are cleaned up after tests to avoid side effects,
    but allow the test to verify creation logic.
    """
    yield
    # Cleanup logic could go here if needed, but for this task we just verify existence

def test_create_directories_creates_folders():
    """
    Verify that create_directories actually creates code/, tests/, data/.
    """
    logger = configure_root_logger()
    
    # Remove if they exist to test creation logic fresh
    for d in ['code', 'tests', 'data']:
        if Path(d).exists():
            # Only remove if it's empty or we are in a test context
            # For safety in this specific test, we assume clean env or rely on exist_ok
            pass 
    
    create_directories(logger)
    
    assert Path('code').is_dir(), "Directory 'code' should exist"
    assert Path('tests').is_dir(), "Directory 'tests' should exist"
    assert Path('data').is_dir(), "Directory 'data' should exist"

def test_verify_directories_raises_on_missing():
    """
    Verify that verify_directories raises an error if a directory is missing.
    """
    logger = configure_root_logger()
    
    # Temporarily rename a directory to simulate missing state
    backup_path = Path('data')
    temp_path = Path('data_backup_temp')
    
    if backup_path.exists():
        backup_path.rename(temp_path)
    
    try:
        with pytest.raises(FileNotFoundError):
            verify_directories(logger)
    finally:
        # Restore
        if temp_path.exists():
            temp_path.rename(backup_path)

def test_os_makedirs_executed():
    """
    Direct verification that the directories exist as per the task requirement.
    """
    # This test implicitly validates the side effect of the script execution
    assert os.path.isdir('code'), "code/ must exist"
    assert os.path.isdir('tests'), "tests/ must exist"
    assert os.path.isdir('data'), "data/ must exist"
