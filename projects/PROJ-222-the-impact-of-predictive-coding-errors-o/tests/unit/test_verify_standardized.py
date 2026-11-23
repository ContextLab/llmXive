"""
Unit tests for T017: verify_standardized.py
"""
import json
import os
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from verify_standardized import (
    verify_columns,
    verify_row_count,
    REQUIRED_COLUMNS,
    MIN_ROWS,
    write_verification_log,
    run_verification
)

@pytest.fixture
def mock_dataframe():
    """Create a mock DataFrame with all required columns and enough rows."""
    data = {
        'duration_estimate': [1.0] * 150,
        'stimulus_sequence': [['a', 'b']] * 150,
        'participant_id': [f'P{i}' for i in range(150)],
        'surprisal': [0.5] * 150,
        'sequence_length': [2] * 150,
        'stimulus_modality': ['visual'] * 150,
        'extra_col': [1] * 150
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_dataframe_missing_cols():
    """Create a mock DataFrame missing some required columns."""
    data = {
        'duration_estimate': [1.0] * 100,
        'participant_id': [f'P{i}' for i in range(100)],
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_dataframe_too_few_rows():
    """Create a mock DataFrame with fewer than MIN_ROWS."""
    data = {
        'duration_estimate': [1.0] * 50,
        'stimulus_sequence': [['a', 'b']] * 50,
        'participant_id': [f'P{i}' for i in range(50)],
        'surprisal': [0.5] * 50,
        'sequence_length': [2] * 50,
        'stimulus_modality': ['visual'] * 50,
    }
    return pd.DataFrame(data)

def test_verify_columns_all_present(mock_dataframe):
    """Test verify_columns when all columns are present."""
    passed, missing = verify_columns(mock_dataframe)
    assert passed is True
    assert missing == []

def test_verify_columns_missing(mock_dataframe_missing_cols):
    """Test verify_columns when some columns are missing."""
    passed, missing = verify_columns(mock_dataframe_missing_cols)
    assert passed is False
    assert len(missing) > 0
    assert 'stimulus_sequence' in missing
    assert 'surprisal' in missing

def test_verify_row_count_sufficient(mock_dataframe):
    """Test verify_row_count when rows are sufficient."""
    passed, count = verify_row_count(mock_dataframe)
    assert passed is True
    assert count == 150

def test_verify_row_count_insufficient(mock_dataframe_too_few_rows):
    """Test verify_row_count when rows are insufficient."""
    passed, count = verify_row_count(mock_dataframe_too_few_rows)
    assert passed is False
    assert count == 50
    assert count < MIN_ROWS

def test_write_verification_log(tmp_path):
    """Test writing the verification log."""
    log_path = tmp_path / "test_log.json"
    details = {
        "timestamp": "2023-01-01T00:00:00",
        "overall_success": True,
        "checks": {"test": "passed"}
    }
    
    write_verification_log(True, details, log_path)
    
    assert log_path.exists()
    with open(log_path, 'r') as f:
        content = json.load(f)
    
    assert isinstance(content, list)
    assert len(content) == 1
    assert content[0]["overall_success"] is True
    assert content[0]["details"]["overall_success"] is True

def test_write_verification_log_append(tmp_path):
    """Test that write_verification_log appends to existing log."""
    log_path = tmp_path / "test_log.json"
    # Create initial log
    initial_log = [{"task_id": "T016", "success": True}]
    with open(log_path, 'w') as f:
        json.dump(initial_log, f)
    
    details = {
        "timestamp": "2023-01-01T00:00:00",
        "overall_success": True,
        "checks": {}
    }
    
    write_verification_log(True, details, log_path)
    
    with open(log_path, 'r') as f:
        content = json.load(f)
    
    assert len(content) == 2
    assert content[0]["task_id"] == "T016"
    assert content[1]["task_id"] == "T017"