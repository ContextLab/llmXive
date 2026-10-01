import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Ensure the code directory is in the path
sys_path_backup = __import__('sys').path.copy()
try:
    __import__('sys').path.insert(0, str(Path(__file__).parent.parent / 'code'))
    
    from pre_ingestion_validation_gate import (
        ensure_directories, 
        check_file_exists, 
        check_directory_exists, 
        run_validation_gate,
        update_project_state
    )
finally:
    __import__('sys').path = sys_path_backup

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    # Create a temp root to avoid polluting the actual project structure during tests
    # We will mock the paths used in the functions
    return tmp_path

def test_check_file_exists_exists(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")
    logger = MagicMock()
    assert check_file_exists(file_path, logger) is True
    logger.error.assert_not_called()

def test_check_file_exists_missing(tmp_path):
    file_path = tmp_path / "missing.txt"
    logger = MagicMock()
    assert check_file_exists(file_path, logger) is False
    logger.error.assert_called_once()

def test_check_file_exists_empty(tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.touch() # Create empty file
    logger = MagicMock()
    assert check_file_exists(file_path, logger) is False
    logger.error.assert_called_once()

def test_check_directory_exists_populated(tmp_path):
    dir_path = tmp_path / "data"
    dir_path.mkdir()
    (dir_path / "file.txt").write_text("content")
    logger = MagicMock()
    assert check_directory_exists(dir_path, logger) is True
    logger.error.assert_not_called()

def test_check_directory_exists_empty(tmp_path):
    dir_path = tmp_path / "empty_dir"
    dir_path.mkdir()
    logger = MagicMock()
    assert check_directory_exists(dir_path, logger) is False
    logger.error.assert_called_once()

def test_check_directory_exists_missing(tmp_path):
    dir_path = tmp_path / "non_existent"
    logger = MagicMock()
    assert check_directory_exists(dir_path, logger) is False
    logger.error.assert_called_once()

@patch('pre_ingestion_validation_gate.check_file_exists')
@patch('pre_ingestion_validation_gate.check_directory_exists')
def test_run_validation_gate_pass(mock_check_dir, mock_check_file, tmp_path):
    # Setup mocks to return True
    mock_check_file.return_value = True
    mock_check_dir.return_value = True

    # Mock paths to point to temp dirs to avoid side effects
    with patch('pre_ingestion_validation_gate.Path') as MockPath:
        # Configure the Path mock to return our temp paths for specific strings
        def path_side_effect(p):
            if p == "data/raw/moral_machine.csv.gz":
                return tmp_path / "moral_machine.csv.gz"
            elif p == "data/raw/era5_raw_chunks":
                return tmp_path / "era5_raw_chunks"
            elif p == "results/logs/data_validation_log.txt":
                return tmp_path / "validation_log.txt"
            return Path(p) # Default behavior for other paths

        MockPath.side_effect = path_side_effect
        
        # Ensure temp paths exist for the mocks to work correctly if needed
        (tmp_path / "moral_machine.csv.gz").write_text("data")
        (tmp_path / "era5_raw_chunks").mkdir()
        (tmp_path / "era5_raw_chunks" / "chunk.txt").write_text("data")

        logger = MagicMock()
        result = run_validation_gate(logger)
        
        assert result is True
        logger.info.assert_called_with("Pre-Ingestion Validation Gate: PASS")

@patch('pre_ingestion_validation_gate.check_file_exists')
@patch('pre_ingestion_validation_gate.check_directory_exists')
def test_run_validation_gate_fail(mock_check_dir, mock_check_file, tmp_path):
    # Setup mocks to return False for one check
    mock_check_file.return_value = False
    mock_check_dir.return_value = True

    with patch('pre_ingestion_validation_gate.Path') as MockPath:
        def path_side_effect(p):
            if p == "data/raw/moral_machine.csv.gz":
                return tmp_path / "moral_machine.csv.gz"
            elif p == "data/raw/era5_raw_chunks":
                return tmp_path / "era5_raw_chunks"
            elif p == "results/logs/data_validation_log.txt":
                return tmp_path / "validation_log.txt"
            return Path(p)

        MockPath.side_effect = path_side_effect
        
        logger = MagicMock()
        result = run_validation_gate(logger)
        
        assert result is False
        logger.error.assert_called_with("Pre-Ingestion Validation Gate: FAIL")
