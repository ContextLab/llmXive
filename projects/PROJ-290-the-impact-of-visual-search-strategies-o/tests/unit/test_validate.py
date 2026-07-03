"""
Unit tests for code/data/validate.py
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np
import pytest

from data.validate import (
    check_variable_presence,
    validate_data_content,
    apply_roi_fallback,
    validate_dataset,
    write_validation_report,
    CRITICAL_VARS
)
from config import get_config

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'gaze_coordinates': [[10, 20], [30, 40], [50, 60]],
        'response_times': [0.5, 0.6, 0.7],
        'emotion_labels': ['happy', 'sad', 'neutral'],
        'roi_annotations': [{'x': 0, 'y': 0, 'w': 100, 'h': 100}],
        'participant_id': ['P1', 'P2', 'P3']
    })

@pytest.fixture
def incomplete_dataframe():
    """Create a DataFrame missing critical variables."""
    return pd.DataFrame({
        'gaze_coordinates': [[10, 20], [30, 40]],
        'response_times': [0.5, 0.6],
        # Missing emotion_labels and roi_annotations
    })

@pytest.fixture
def empty_dataframe():
    """Create a DataFrame with empty critical variables."""
    return pd.DataFrame({
        'gaze_coordinates': [None, None],
        'response_times': [None, None],
        'emotion_labels': [None, None],
    })

def test_check_variable_presence_all_present(sample_dataframe):
    """Test checking presence when all variables are present."""
    result = check_variable_presence(sample_dataframe, CRITICAL_VARS)
    for var in CRITICAL_VARS:
        assert result[var] is True

def test_check_variable_presence_missing_vars(incomplete_dataframe):
    """Test checking presence when some variables are missing."""
    result = check_variable_presence(incomplete_dataframe, CRITICAL_VARS)
    assert result['gaze_coordinates'] is True
    assert result['response_times'] is True
    assert result['emotion_labels'] is False

def test_validate_data_content_valid(sample_dataframe):
    """Test validation of data content for valid variables."""
    for var in CRITICAL_VARS:
        assert validate_data_content(sample_dataframe, var) is True

def test_validate_data_content_empty(empty_dataframe):
    """Test validation of data content for empty variables."""
    for var in CRITICAL_VARS:
        assert validate_data_content(empty_dataframe, var) is False

def test_validate_data_content_nonexistent(sample_dataframe):
    """Test validation of a non-existent variable."""
    assert validate_data_content(sample_dataframe, 'nonexistent_var') is False

def test_apply_roi_fallback(sample_dataframe):
    """Test applying ROI fallback."""
    # Remove roi_annotations
    df_no_roi = sample_dataframe.drop(columns=['roi_annotations'])
    
    # Apply fallback
    result_df = apply_roi_fallback(df_no_roi)
    
    assert 'roi_annotations' in result_df.columns
    assert len(result_df) == len(sample_dataframe)

def test_write_validation_report():
    """Test writing validation report to file."""
    report = {
        'status': 'PASS',
        'test': 'value'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        write_validation_report(report, temp_path)
        
        assert temp_path.exists()
        
        with open(temp_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report['status'] == 'PASS'
        assert loaded_report['test'] == 'value'
    finally:
        temp_path.unlink()

def test_validate_dataset_with_valid_data(sample_dataframe):
    """Test full validation with valid data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        dataset_path = tmpdir_path / "test_dataset.csv"
        output_path = tmpdir_path / "validation_report.json"
        
        # Save sample data
        sample_dataframe.to_csv(dataset_path, index=False)
        
        # Mock get_config to return our temp directory
        with patch('data.validate.get_config') as mock_config:
            mock_config.return_value.data_dir = str(tmpdir_path)
            
            report = validate_dataset(dataset_path, output_path)
            
            assert report['status'] == 'PASS'
            assert 'missing_critical_vars' in report
            assert len(report['missing_critical_vars']) == 0
            assert output_path.exists()

def test_validate_dataset_with_missing_critical(incomplete_dataframe):
    """Test full validation with missing critical variables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        dataset_path = tmpdir_path / "test_dataset.csv"
        output_path = tmpdir_path / "validation_report.json"
        
        # Save incomplete data
        incomplete_dataframe.to_csv(dataset_path, index=False)
        
        # Mock get_config
        with patch('data.validate.get_config') as mock_config:
            mock_config.return_value.data_dir = str(tmpdir_path)
            
            # Should exit with code 1 due to missing critical vars
            with pytest.raises(SystemExit) as exc_info:
                validate_dataset(dataset_path, output_path)
            
            assert exc_info.value.code == 1
