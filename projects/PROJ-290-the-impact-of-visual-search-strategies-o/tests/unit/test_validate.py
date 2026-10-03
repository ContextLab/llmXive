import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile
import logging

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.validate import (
    check_variable_presence,
    validate_data_content,
    apply_roi_fallback,
    write_validation_report,
    validate_dataset
)
from utils.logging import get_logger

@pytest.fixture
def sample_df_with_all_vars():
    """Create a sample dataframe with all required variables."""
    data = {
        'gaze_coordinates': [[10, 20], [30, 40], [50, 60]],
        'response_times': [0.5, 0.7, 0.6],
        'emotion_labels': ['happy', 'sad', 'neutral'],
        'roi_annotations': ['grid_3x3', 'grid_3x3', 'grid_3x3']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing_roi():
    """Create a sample dataframe missing roi_annotations."""
    data = {
        'gaze_coordinates': [[10, 20], [30, 40]],
        'response_times': [0.5, 0.7],
        'emotion_labels': ['happy', 'sad']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_missing_critical():
    """Create a sample dataframe missing a critical variable (response_times)."""
    data = {
        'gaze_coordinates': [[10, 20], [30, 40]],
        'emotion_labels': ['happy', 'sad'],
        'roi_annotations': ['grid', 'grid']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_empty():
    """Create an empty dataframe."""
    return pd.DataFrame()

@pytest.fixture
def sample_df_null_critical():
    """Create a dataframe with null values in a critical variable."""
    data = {
        'gaze_coordinates': [[10, 20], [30, 40]],
        'response_times': [np.nan, np.nan],
        'emotion_labels': ['happy', 'sad'],
        'roi_annotations': ['grid', 'grid']
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_output_path():
    """Create a temporary file path for the report."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        yield Path(f.name)
    os.unlink(f.name)

@pytest.fixture
def logger():
    return get_logger("test_validate")

def test_check_variable_presence_all_present(sample_df_with_all_vars, logger):
    """Test that all present variables are detected correctly."""
    required = ['gaze_coordinates', 'response_times', 'emotion_labels', 'roi_annotations']
    present, missing = check_variable_presence(sample_df_with_all_vars, required, logger)
    
    assert len(missing) == 0
    assert set(present) == set(required)

def test_check_variable_presence_missing_one(sample_df_missing_roi, logger):
    """Test detection of a single missing variable."""
    required = ['gaze_coordinates', 'response_times', 'emotion_labels', 'roi_annotations']
    present, missing = check_variable_presence(sample_df_missing_roi, required, logger)
    
    assert 'roi_annotations' in missing
    assert len(missing) == 1
    assert len(present) == 3

def test_validate_data_content_empty_df(sample_df_empty, logger):
    """Test that an empty dataframe fails validation."""
    required = ['gaze_coordinates', 'response_times', 'emotion_labels']
    result = validate_data_content(sample_df_empty, required, logger)
    assert result is False

def test_validate_data_content_null_critical(sample_df_null_critical, logger):
    """Test that null values in critical variables fail validation."""
    required = ['gaze_coordinates', 'response_times', 'emotion_labels']
    result = validate_data_content(sample_df_null_critical, required, logger)
    assert result is False

def test_validate_data_content_valid(sample_df_with_all_vars, logger):
    """Test that valid data passes content validation."""
    required = ['gaze_coordinates', 'response_times', 'emotion_labels']
    result = validate_data_content(sample_df_with_all_vars, required, logger)
    assert result is True

def test_apply_roi_fallback_missing(sample_df_missing_roi, logger):
    """Test that ROI fallback adds the column when missing."""
    df = sample_df_missing_roi.copy()
    result_df = apply_roi_fallback(df, logger)
    
    assert 'roi_annotations' in result_df.columns
    assert len(result_df) == len(sample_df_missing_roi)

def test_apply_roi_fallback_present(sample_df_with_all_vars, logger):
    """Test that ROI fallback does nothing when column exists."""
    df = sample_df_with_all_vars.copy()
    original_len = len(df)
    result_df = apply_roi_fallback(df, logger)
    
    assert 'roi_annotations' in result_df.columns
    # Should not modify the data, just confirm it exists
    assert result_df['roi_annotations'].iloc[0] == 'grid_3x3'

def test_write_validation_report(temp_output_path, logger):
    """Test that the validation report is written correctly."""
    status = "PASS"
    missing = []
    present = ['gaze_coordinates', 'response_times']
    total = 10
    valid = 10
    roi_fallback = False
    
    write_validation_report(
        output_path=temp_output_path,
        status=status,
        missing_vars=missing,
        present_vars=present,
        total_records=total,
        valid_records=valid,
        roi_fallback_applied=roi_fallback,
        logger=logger
    )
    
    assert temp_output_path.exists()
    with open(temp_output_path, 'r') as f:
        report = json.load(f)
    
    assert report['status'] == status
    assert report['missing_variables'] == missing
    assert report['present_variables'] == present
    assert report['statistics']['total_records'] == total

def test_validate_dataset_critical_missing_raises(sample_df_missing_critical, temp_output_path, logger):
    """Test that validate_dataset raises an error when critical vars are missing."""
    with pytest.raises(ValueError, match="Validation failed"):
        validate_dataset(sample_df_missing_critical, temp_output_path, logger)

def test_validate_dataset_full_success(sample_df_with_all_vars, temp_output_path, logger):
    """Test that a full valid dataset passes without error."""
    result = validate_dataset(sample_df_with_all_vars, temp_output_path, logger)
    assert result is True
    assert temp_output_path.exists()
    
    with open(temp_output_path, 'r') as f:
        report = json.load(f)
    assert report['status'] == 'PASS'

def test_validate_dataset_missing_roi_fallback_success(sample_df_missing_roi, temp_output_path, logger):
    """Test that missing ROI triggers fallback and passes validation."""
    result = validate_dataset(sample_df_missing_roi, temp_output_path, logger)
    assert result is True
    
    with open(temp_output_path, 'r') as f:
        report = json.load(f)
    assert report['roi_fallback_applied'] is True
    assert report['status'] == 'PASS'