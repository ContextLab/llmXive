import os
import csv
import tempfile
from pathlib import Path
import pytest

from code.data.verify_output import verify_csv_artifact, verify_log_artifact

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        processed_dir = data_dir / "processed"
        raw_dir = data_dir / "raw"
        processed_dir.mkdir()
        raw_dir.mkdir()
        yield data_dir

def test_verify_csv_artifact_exists_and_valid(temp_data_dir):
    """Test that a valid CSV file passes verification."""
    csv_path = temp_data_dir / "processed" / "test.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['col1', 'col2', 'col3'])
        writer.writeheader()
        writer.writerow({'col1': 'a', 'col2': 'b', 'col3': 'c'})
        writer.writerow({'col1': 'd', 'col2': 'e', 'col3': 'f'})
    
    result = verify_csv_artifact(
        "processed/test.csv",
        required_columns=['col1', 'col2'],
        min_rows=1
    )
    
    assert result['exists'] is True
    assert result['is_valid'] is True
    assert result['row_count'] == 2
    assert len(result['missing_columns']) == 0
    assert len(result['errors']) == 0

def test_verify_csv_artifact_missing_file(temp_data_dir):
    """Test that a missing CSV file fails verification."""
    result = verify_csv_artifact(
        "processed/nonexistent.csv",
        required_columns=['col1'],
        min_rows=1
    )
    
    assert result['exists'] is False
    assert result['is_valid'] is False
    assert len(result['errors']) == 1
    assert "does not exist" in result['errors'][0]

def test_verify_csv_artifact_missing_columns(temp_data_dir):
    """Test that a CSV with missing required columns fails verification."""
    csv_path = temp_data_dir / "processed" / "test.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
        writer.writeheader()
        writer.writerow({'col1': 'a', 'col2': 'b'})
    
    result = verify_csv_artifact(
        "processed/test.csv",
        required_columns=['col1', 'col3'],  # col3 is missing
        min_rows=1
    )
    
    assert result['exists'] is True
    assert result['is_valid'] is False
    assert 'col3' in result['missing_columns']
    assert len(result['errors']) == 1

def test_verify_log_artifact_exists(temp_data_dir):
    """Test that a valid log file passes verification."""
    log_path = temp_data_dir / "raw" / "test.log"
    log_path.write_text("Line 1\nLine 2\nLine 3\n")
    
    result = verify_log_artifact(
        "raw/test.log",
        min_lines=2
    )
    
    assert result['exists'] is True
    assert result['is_valid'] is True
    assert result['line_count'] == 3

def test_verify_log_artifact_missing_file(temp_data_dir):
    """Test that a missing log file fails verification."""
    result = verify_log_artifact(
        "raw/nonexistent.log",
        min_lines=1
    )
    
    assert result['exists'] is False
    assert result['is_valid'] is False
    assert len(result['errors']) == 1

def test_verify_log_artifact_insufficient_lines(temp_data_dir):
    """Test that a log with too few lines fails verification."""
    log_path = temp_data_dir / "raw" / "test.log"
    log_path.write_text("Single line\n")
    
    result = verify_log_artifact(
        "raw/test.log",
        min_lines=5
    )
    
    assert result['exists'] is True
    assert result['is_valid'] is False
    assert len(result['errors']) == 1
    assert "fewer lines than expected" in result['errors'][0]
