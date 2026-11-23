import pytest
import json
import tempfile
from pathlib import Path
import pandas as pd

# Import functions to test
from download import (
    compute_sha256,
    parse_dataset_ids,
    filter_dataset_columns,
    write_exclusion_log,
    write_blocked_status
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_csv(temp_dir):
    """Create a sample CSV file for testing."""
    csv_path = temp_dir / "sample.csv"
    df = pd.DataFrame({
        'duration_estimate': [1.0, 2.0, 3.0],
        'stimulus_sequence': ['A', 'B', 'C'],
        'participant_id': ['P1', 'P1', 'P2'],
        'extra_col': [4, 5, 6]
    })
    df.to_csv(csv_path, index=False)
    return csv_path

def test_compute_sha256(temp_dir):
    """Test SHA256 checksum computation."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("Hello, World!")
    
    checksum = compute_sha256(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_parse_dataset_ids(temp_dir):
    """Test parsing dataset IDs from file."""
    ids_file = temp_dir / "ids.txt"
    ids_file.write_text("123\n456\n# comment\n789\n")
    
    ids = parse_dataset_ids(ids_file)
    assert ids == ["123", "456", "789"]

def test_parse_dataset_ids_missing_file(temp_dir):
    """Test parsing when file doesn't exist."""
    ids_file = temp_dir / "nonexistent.txt"
    ids = parse_dataset_ids(ids_file)
    assert ids == []

def test_filter_dataset_columns_valid(sample_csv):
    """Test filtering with valid columns."""
    required = ['duration_estimate', 'stimulus_sequence', 'participant_id']
    result = filter_dataset_columns(sample_csv, required)
    assert result is True

def test_filter_dataset_columns_missing(sample_csv):
    """Test filtering with missing columns."""
    required = ['duration_estimate', 'stimulus_sequence', 'participant_id', 'nonexistent']
    result = filter_dataset_columns(sample_csv, required)
    assert result is False

def test_write_exclusion_log(temp_dir):
    """Test writing exclusion log."""
    exclusions = [
        {'dataset_id': '123', 'status': 'excluded', 'reason': 'test reason'}
    ]
    log_path = temp_dir / "exclusion_log.json"
    
    write_exclusion_log(exclusions, log_path)
    
    assert log_path.exists()
    with open(log_path, 'r') as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]['dataset_id'] == '123'

def test_write_blocked_status(temp_dir):
    """Test writing blocked status."""
    status_path = temp_dir / "blocked_status.json"
    
    write_blocked_status("Test reason", status_path)
    
    assert status_path.exists()
    with open(status_path, 'r') as f:
        data = json.load(f)
    assert data['status'] == 'blocked'
    assert data['reason'] == 'Test reason'
