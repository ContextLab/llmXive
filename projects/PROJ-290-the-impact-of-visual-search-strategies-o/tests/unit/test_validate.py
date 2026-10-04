"""
Unit tests for data validation module (T012).

Tests:
- Variable presence checking
- ROI fallback application
- Report generation
- Halting on missing critical variables
"""
import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
import logging

from code.data.validate import (
    check_variable_presence,
    validate_data_content,
    apply_roi_fallback,
    write_validation_report,
    validate_dataset,
    CRITICAL_VARIABLES
)
from code.config import get_config

@pytest.fixture
def sample_data_with_all_vars():
    """Sample DataFrame with all critical variables."""
    return pd.DataFrame({
        'gaze_coordinates': [[100, 200], [150, 250], [120, 220]],
        'response_times': [0.5, 0.7, 0.6],
        'emotion_labels': ['happy', 'sad', 'angry'],
        'roi_annotations': [{'eye': [0, 0]}, {'eye': [1, 1]}, {'eye': [2, 2]}],
        'participant_id': [1, 2, 3]
    })

@pytest.fixture
def sample_data_missing_vars():
    """Sample DataFrame missing some critical variables."""
    return pd.DataFrame({
        'gaze_coordinates': [[100, 200], [150, 250]],
        'response_times': [0.5, 0.7],
        # Missing emotion_labels and roi_annotations
        'participant_id': [1, 2]
    })

@pytest.fixture
def sample_data_empty():
    """Empty DataFrame."""
    return pd.DataFrame()

@pytest.fixture
def temp_output_path():
    """Temporary path for report output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / 'test_report.json'

def test_check_variable_presence_all_present(sample_data_with_all_vars):
    """Test that all_present is True when all variables exist."""
    all_present, missing = check_variable_presence(sample_data_with_all_vars, CRITICAL_VARIABLES)
    assert all_present is True
    assert len(missing) == 0

def test_check_variable_presence_some_missing(sample_data_missing_vars):
    """Test detection of missing variables."""
    all_present, missing = check_variable_presence(sample_data_missing_vars, CRITICAL_VARIABLES)
    assert all_present is False
    assert 'emotion_labels' in missing
    assert 'roi_annotations' in missing

def test_validate_data_content_non_empty(sample_data_with_all_vars):
    """Test content validation on non-empty data."""
    result = validate_data_content(sample_data_with_all_vars)
    assert result['is_empty'] is False
    assert result['row_count'] == 3

def test_validate_data_content_empty(sample_data_empty):
    """Test content validation on empty data."""
    result = validate_data_content(sample_data_empty)
    assert result['is_empty'] is True
    assert len(result['issues']) > 0

def test_apply_roi_fallback_when_missing(sample_data_missing_vars):
    """Test that ROI fallback is applied when roi_annotations is missing."""
    result = apply_roi_fallback(sample_data_missing_vars)
    assert 'roi_annotations' in result.columns
    # Check that the default 3x3 grid was applied
    assert len(result['roi_annotations'][0]) == 9

def test_apply_roi_fallback_when_present(sample_data_with_all_vars):
    """Test that ROI fallback is NOT applied when roi_annotations exists."""
    original_roi = sample_data_with_all_vars['roi_annotations'].iloc[0]
    result = apply_roi_fallback(sample_data_with_all_vars)
    # Should remain unchanged
    assert result['roi_annotations'].iloc[0] == original_roi

def test_write_validation_report(temp_output_path):
    """Test that validation report is written correctly."""
    test_result = {
        'status': 'passed',
        'missing_variables': [],
        'test_field': 'test_value'
    }
    write_validation_report(test_result, temp_output_path)
    
    assert temp_output_path.exists()
    with open(temp_output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded['status'] == 'passed'
    assert loaded['test_field'] == 'test_value'

def test_validate_dataset_raises_on_missing_critical_vars(sample_data_missing_vars, tmp_path):
    """Test that validate_dataset raises ValueError when critical vars are missing."""
    # Create a mock config with a temp data dir
    class MockConfig:
        DATA_DIR = str(tmp_path)
    
    with pytest.raises(ValueError) as excinfo:
        validate_dataset(sample_data_missing_vars, MockConfig())
    
    assert "Missing required variables" in str(excinfo.value)
    assert "emotion_labels" in str(excinfo.value)

def test_validate_dataset_passes_when_all_present(sample_data_with_all_vars, tmp_path):
    """Test that validate_dataset passes when all critical vars are present."""
    class MockConfig:
        DATA_DIR = str(tmp_path)
    
    result = validate_dataset(sample_data_with_all_vars, MockConfig())
    assert result['status'] == 'passed'
    assert len(result['missing_variables']) == 0
    assert (tmp_path / 'validation_report.json').exists()

def test_roi_fallback_creates_3x3_grid_structure():
    """Test that the fallback ROI is a 3x3 grid (9 regions)."""
    df = pd.DataFrame({'id': [1, 2]})
    result = apply_roi_fallback(df)
    
    roi = result['roi_annotations'].iloc[0]
    assert len(roi) == 9
    
    # Check labels for 3x3 grid
    labels = [r['label'] for r in roi]
    expected_labels = [
        'top_left', 'top_center', 'top_right',
        'middle_left', 'center', 'middle_right',
        'bottom_left', 'bottom_center', 'bottom_right'
    ]
    assert labels == expected_labels