import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_directories import setup_directories

def test_setup_directories_creates_processed():
    """
    Test that setup_directories creates the data/processed directory
    as required by T008b.
    """
    # Run the setup
    result = setup_directories()
    assert result is True

    # Verify the specific directory for T008b exists
    # The script calculates project_root relative to itself.
    # If running from tests, we need to ensure we check the right path.
    # setup_directories() uses Path(__file__).resolve().parent of setup_directories.py
    # which is code/. So project_root is the project root.
    
    # We can verify by checking if the function returns True and 
    # the directory exists relative to the code folder.
    current_file_dir = Path(__file__).parent.parent
    processed_dir = current_file_dir / "data" / "processed"
    
    assert processed_dir.exists(), "data/processed directory must exist after setup"
    assert processed_dir.is_dir(), "data/processed must be a directory"

def test_setup_directories_creates_raw():
    """
    Test that setup_directories creates the data/raw directory (T008a).
    """
    result = setup_directories()
    assert result is True

    current_file_dir = Path(__file__).parent.parent
    raw_dir = current_file_dir / "data" / "raw"
    
    assert raw_dir.exists(), "data/raw directory must exist after setup"
    assert raw_dir.is_dir(), "data/raw must be a directory"

def test_setup_directories_creates_code_modules():
    """
    Test that setup_directories creates code/data and code/models (T008c, T008d).
    """
    result = setup_directories()
    assert result is True

    current_file_dir = Path(__file__).parent.parent
    code_data = current_file_dir / "code" / "data"
    code_models = current_file_dir / "code" / "models"
    
    assert code_data.exists(), "code/data directory must exist"
    assert code_models.exists(), "code/models directory must exist"

def test_setup_directories_creates_tests():
    """
    Test that setup_directories creates the tests directory (T008e).
    """
    result = setup_directories()
    assert result is True

    current_file_dir = Path(__file__).parent.parent
    tests_dir = current_file_dir / "tests"
    
    assert tests_dir.exists(), "tests directory must exist"
    assert tests_dir.is_dir(), "tests must be a directory"

def test_idempotency():
    """
    Test that running setup_directories twice does not raise errors.
    """
    result1 = setup_directories()
    result2 = setup_directories()
    
    assert result1 is True
    assert result2 is True