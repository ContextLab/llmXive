import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from spec_deviation_handler import (
    get_deviations_path,
    load_deviations,
    save_deviations,
    record_spec_deviation_fr002,
    record_spec_deviation_fr003,
    main
)

@pytest.fixture
def temp_deviation_files(tmp_path):
    """Create temporary paths for logs and artifacts."""
    logs_dir = tmp_path / "logs"
    artifacts_dir = tmp_path / "artifacts"
    logs_dir.mkdir()
    artifacts_dir.mkdir()
    
    # Patch the global paths
    original_log_path = Path("logs/deviation.log")
    original_json_path = Path("artifacts/spec_deviations.json")
    
    # We need to mock the module-level constants or the functions that use them
    # Since the functions use hardcoded paths, we will patch the file operations
    # or run the test in a way that ensures the files are created in temp_dir
    # For simplicity in this test, we will verify file creation side-effects
    # by checking if the files exist after calling the functions, 
    # but we need to ensure the paths are writable.
    # A better approach for unit tests is to refactor to accept paths, 
    # but per "Extend, don't re-author", we test the side effects assuming 
    # the environment allows writing to logs/ and artifacts/ (which T001 ensures).
    
    return logs_dir, artifacts_dir

def test_record_spec_deviation_fr002_creates_log_entry(temp_deviation_files):
    """Test that FR-002 is logged correctly."""
    logs_dir, artifacts_dir = temp_deviation_files
    
    # Ensure the logs directory exists in the expected relative path for the test
    # We will create the files in the temp dir and then check content
    # However, the function writes to hardcoded "logs/deviation.log"
    # To make this test robust without changing the code, we assume the test runner
    # has write access to the project root logs/ and artifacts/ directories.
    # If running in isolation, we might need to patch the path constants.
    
    # Mocking the Path operations to write to temp_dir
    with patch('spec_deviation_handler.DEVIATIONS_LOG_PATH', logs_dir / "deviation.log"):
        with patch('spec_deviation_handler.DEVIATIONS_JSON_PATH', artifacts_dir / "spec_deviations.json"):
            with patch('spec_deviation_handler.setup_logging') as mock_logger:
                mock_logger_instance = MagicMock()
                mock_logger.return_value = mock_logger_instance
                
                record_spec_deviation_fr002(mock_logger_instance)
                
                # Verify logger was called
                mock_logger_instance.warning.assert_called()
                
                # Verify log file content
                log_file = logs_dir / "deviation.log"
                assert log_file.exists(), "deviation.log should be created"
                with open(log_file, 'r') as f:
                    content = f.read()
                    assert "FR-002" in content
                    assert "ISRIC merge excluded" in content
                
                # Verify JSON file content
                json_file = artifacts_dir / "spec_deviations.json"
                assert json_file.exists(), "spec_deviations.json should be created"
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    assert len(data) >= 1
                    assert any(d['id'] == 'FR-002' for d in data)

def test_record_spec_deviation_fr003_creates_log_entry(temp_deviation_files):
    """Test that FR-003 is logged correctly."""
    logs_dir, artifacts_dir = temp_deviation_files
    
    with patch('spec_deviation_handler.DEVIATIONS_LOG_PATH', logs_dir / "deviation.log"):
        with patch('spec_deviation_handler.DEVIATIONS_JSON_PATH', artifacts_dir / "spec_deviations.json"):
            with patch('spec_deviation_handler.setup_logging') as mock_logger:
                mock_logger_instance = MagicMock()
                mock_logger.return_value = mock_logger_instance
                
                record_spec_deviation_fr003(mock_logger_instance)
                
                mock_logger_instance.warning.assert_called()
                
                log_file = logs_dir / "deviation.log"
                with open(log_file, 'r') as f:
                    content = f.read()
                    assert "FR-003" in content
                    assert "KNN imputation excluded" in content

def test_load_deviations_empty_when_missing(temp_deviation_files):
    """Test loading deviations when file doesn't exist."""
    with patch('spec_deviation_handler.DEVIATIONS_JSON_PATH', temp_deviation_files[1] / "nonexistent.json"):
        result = load_deviations()
        assert result == []