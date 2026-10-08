import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

from data.retention_validation import (
    load_retention_metrics,
    load_behavioral_data,
    validate_retention_threshold,
    save_retention_metrics,
    run_retention_validation,
    REQUIRED_BEHAVIORAL_COLUMNS
)

@pytest.fixture
def valid_metadata_csv(tmp_path):
    """Create a valid metadata CSV file."""
    data = {
        'subject_id': ['sub-001', 'sub-002', 'sub-003', 'sub-004'],
        'pre_motor_score': [10.5, 12.0, 9.8, 11.2],
        'post_motor_score': [15.0, 16.5, 14.2, 15.8],
        'age': [25, 30, 28, 32],
        'sex': ['M', 'F', 'M', 'F']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "metadata.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def incomplete_metadata_csv(tmp_path):
    """Create a metadata CSV with missing behavioral data."""
    data = {
        'subject_id': ['sub-001', 'sub-002', 'sub-003', 'sub-004'],
        'pre_motor_score': [10.5, None, 9.8, 11.2],  # sub-002 missing
        'post_motor_score': [15.0, 16.5, None, 15.8], # sub-003 missing
        'age': [25, 30, 28, 32],
        'sex': ['M', 'F', 'M', 'F']
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "metadata_incomplete.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def missing_columns_csv(tmp_path):
    """Create a metadata CSV missing required columns."""
    data = {
        'subject_id': ['sub-001', 'sub-002'],
        'age': [25, 30],
        # Missing pre_motor_score, post_motor_score, sex
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "metadata_missing_cols.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_load_retention_metrics_valid(valid_metadata_csv):
    """Test loading a valid metadata CSV."""
    df = load_retention_metrics(valid_metadata_csv)
    assert len(df) == 4
    assert 'subject_id' in df.columns
    assert 'pre_motor_score' in df.columns

def test_load_retention_metrics_missing_file(tmp_path):
    """Test loading a non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_retention_metrics(str(tmp_path / "nonexistent.csv"))

def test_load_behavioral_data_valid(valid_metadata_csv):
    """Test behavioral data extraction with all valid data."""
    df = load_retention_metrics(valid_metadata_csv)
    valid_df, excluded = load_behavioral_data(df)
    assert len(valid_df) == 4
    assert len(excluded) == 0

def test_load_behavioral_data_incomplete(incomplete_metadata_csv):
    """Test behavioral data extraction with missing values."""
    df = load_retention_metrics(incomplete_metadata_csv)
    valid_df, excluded = load_behavioral_data(df)
    # sub-002 and sub-003 should be excluded
    assert len(valid_df) == 2
    assert len(excluded) == 2
    assert 'sub-002' in excluded
    assert 'sub-003' in excluded

def test_validate_retention_threshold_pass():
    """Test retention threshold validation when passing."""
    passes, reason = validate_retention_threshold(100, 90, 0.80)
    assert passes is True
    assert "met" in reason

def test_validate_retention_threshold_fail():
    """Test retention threshold validation when failing."""
    passes, reason = validate_retention_threshold(100, 50, 0.80)
    assert passes is False
    assert "below" in reason

def test_save_retention_metrics(tmp_path):
    """Test saving retention metrics to JSON."""
    output_path = str(tmp_path / "retention_metrics.json")
    save_retention_metrics(output_path, 0.90, 100, 90)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['retention_rate'] == 0.90
    assert data['total_subjects'] == 100
    assert data['retained_subjects'] == 90
    assert data['status'] == 'passed'

def test_run_retention_validation_success(valid_metadata_csv, tmp_path):
    """Test full validation pipeline with valid data."""
    output_path = str(tmp_path / "retention_metrics.json")
    result = run_retention_validation(valid_metadata_csv, output_path)
    assert result is True
    assert os.path.exists(output_path)

def test_run_retention_validation_missing_columns(missing_columns_csv, tmp_path):
    """Test full validation pipeline fails on missing columns."""
    output_path = str(tmp_path / "retention_metrics.json")
    with pytest.raises(SystemExit) as exc_info:
        run_retention_validation(missing_columns_csv, output_path)
    assert "Fatal" in str(exc_info.value)
    assert "lacks behavioral motor task metrics" in str(exc_info.value)

def test_run_retention_validation_low_retention(incomplete_metadata_csv, tmp_path):
    """Test full validation pipeline fails on low retention."""
    # Create a scenario where retention is < 80%
    # With 4 subjects and 2 excluded, retention is 50%
    output_path = str(tmp_path / "retention_metrics.json")
    with pytest.raises(SystemExit) as exc_info:
        run_retention_validation(incomplete_metadata_csv, output_path)
    assert "Fatal" in str(exc_info.value)
    assert "missing behavioral data" in str(exc_info.value)