import os
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module and constants
from utils.logging import (
    log_exclusion,
    REASON_MISSING_SCAN,
    REASON_MISSING_SCORE,
    REASON_HIGH_MOTION
)
from config import get_config

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory to act as DATA_PATH for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def test_log_exclusion_creates_file_with_header(temp_data_dir):
    """Test that log_exclusion creates the file and writes the header if it doesn't exist."""
    mock_config = MagicMock()
    mock_config.DATA_PATH = temp_data_dir
    
    with patch('utils.logging.get_config', return_value=mock_config):
        log_exclusion(REASON_MISSING_SCAN, "SUBJ_001")
    
    log_path = Path(temp_data_dir) / "data_exclusion_log.txt"
    assert log_path.exists()
    
    with open(log_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
    assert len(rows) == 2  # Header + 1 data row
    assert rows[0] == ['subject_id', 'reason', 'timestamp']
    assert rows[1][0] == "SUBJ_001"
    assert rows[1][1] == REASON_MISSING_SCAN
    assert len(rows[1][2]) > 0  # Timestamp should not be empty

def test_log_exclusion_appends_to_existing_file(temp_data_dir):
    """Test that log_exclusion appends to an existing file."""
    mock_config = MagicMock()
    mock_config.DATA_PATH = temp_data_dir
    
    with patch('utils.logging.get_config', return_value=mock_config):
        # Write first entry
        log_exclusion(REASON_MISSING_SCORE, "SUBJ_002")
        # Write second entry
        log_exclusion(REASON_HIGH_MOTION, "SUBJ_003")
    
    log_path = Path(temp_data_dir) / "data_exclusion_log.txt"
    assert log_path.exists()
    
    with open(log_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
    assert len(rows) == 3  # Header + 2 data rows
    assert rows[1][0] == "SUBJ_002"
    assert rows[1][1] == REASON_MISSING_SCORE
    assert rows[2][0] == "SUBJ_003"
    assert rows[2][1] == REASON_HIGH_MOTION

def test_standardized_reason_codes_exist():
    """Test that the standardized reason codes are defined."""
    assert REASON_MISSING_SCAN == "MISSING_SCAN"
    assert REASON_MISSING_SCORE == "MISSING_SCORE"
    assert REASON_HIGH_MOTION == "HIGH_MOTION"

def test_log_exclusion_custom_filename(temp_data_dir):
    """Test that log_exclusion respects a custom output filename."""
    mock_config = MagicMock()
    mock_config.DATA_PATH = temp_data_dir
    
    custom_filename = "custom_exclusion_log.csv"
    
    with patch('utils.logging.get_config', return_value=mock_config):
        log_exclusion(REASON_MISSING_SCAN, "SUBJ_004", output_filename=custom_filename)
    
    log_path = Path(temp_data_dir) / custom_filename
    assert log_path.exists()
