import os
import csv
import tempfile
from pathlib import Path

import pytest

# We need to mock the config to point to a temp directory for testing
from unittest.mock import patch, MagicMock

# Import the function to test
from code.utils.logging import log_exclusion


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data dir."""
    data_dir = tmp_path / "data"
    interim_dir = data_dir / "interim"
    interim_dir.mkdir(parents=True)
    return data_dir


def test_log_exclusion_creates_file_and_header(temp_data_dir):
    """Test that log_exclusion creates the file with headers if it doesn't exist."""
    log_path = temp_data_dir / "interim" / "data_exclusion_log.txt"
    
    with patch('code.utils.logging.get_config') as mock_config:
        mock_config.return_value.DATA_PATH = str(temp_data_dir)
        
        log_exclusion(reason="MISSING_SCAN", subject_id="SUBJ_001")
        
        assert log_path.exists()
        
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]['reason'] == 'MISSING_SCAN'
            assert rows[0]['subject_id'] == 'SUBJ_001'


def test_log_exclusion_appends_without_header(temp_data_dir):
    """Test that log_exclusion appends to an existing file."""
    log_path = temp_data_dir / "interim" / "data_exclusion_log.txt"
    
    # Create initial file
    log_path.touch()
    with open(log_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "reason", "subject_id"])
        writer.writeheader()
        writer.writerow({"timestamp": None, "reason": "INITIAL", "subject_id": "SUBJ_000"})
    
    with patch('code.utils.logging.get_config') as mock_config:
        mock_config.return_value.DATA_PATH = str(temp_data_dir)
        
        log_exclusion(reason="HIGH_MOTION", subject_id="SUBJ_002")
        
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 2
            assert rows[1]['reason'] == 'HIGH_MOTION'
            assert rows[1]['subject_id'] == 'SUBJ_002'