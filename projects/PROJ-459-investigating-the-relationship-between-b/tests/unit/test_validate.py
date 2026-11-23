"""
Unit tests for data validation functions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from data.validate import (
    exclude_subjects_by_missing_data,
    DataValidationError,
    check_data_integrity
)

@pytest.fixture
def sample_participants():
    """Create a sample participants DataFrame for testing."""
    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05'],
        'musical_genre': [5, 3, np.nan, 4, 2],
        'STOMP-R': [4, np.nan, 3, 5, 3],
        'age': [25, 30, 35, 28, 32],
        'sex': ['M', 'F', 'M', 'F', 'M']
    }
    return pd.DataFrame(data)

@pytest.fixture
def fmriprep_dir(tmp_path):
    """Create a temporary fMRIPrep directory structure for testing."""
    # Create sub-01 directory
    sub_dir = tmp_path / 'sub-01'
    sub_dir.mkdir()
    
    # Create a simple BOLD file (in real usage, this would be a .nii.gz)
    bold_file = sub_dir / 'func' / 'sub-01_task-rest_bold.nii.gz'
    bold_file.parent.mkdir(parents=True)
    
    # Create a dummy file
    with open(bold_file, 'w') as f:
        f.write("dummy")
    
    return tmp_path

def test_exclude_subjects_by_missing_data_behavioral(sample_participants):
    """Test exclusion based on missing behavioral data."""
    # sub-03 has NaN in both musical_genre and STOMP-R (100% missing)
    filtered_df, excluded_ids, reasons = exclude_subjects_by_missing_data(
        sample_participants,
        missing_threshold=0.10
    )
    
    assert 'sub-03' in excluded_ids
    assert len(filtered_df) == 4
    assert 'sub-03' not in filtered_df['participant_id'].values
    
    # Check reason
    assert 'Behavioral data missing' in reasons['sub-03']

def test_exclude_subjects_by_missing_data_all_present():
    """Test when all data is present - no exclusions."""
    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03'],
        'musical_genre': [5, 3, 4],
        'STOMP-R': [4, 3, 5]
    }
    df = pd.DataFrame(data)
    
    filtered_df, excluded_ids, reasons = exclude_subjects_by_missing_data(
        df,
        missing_threshold=0.10
    )
    
    assert len(excluded_ids) == 0
    assert len(filtered_df) == 3
    assert len(reasons) == 0

def test_exclude_subjects_by_missing_data_empty_dataframe():
    """Test with empty DataFrame raises error."""
    df = pd.DataFrame(columns=['participant_id', 'musical_genre'])
    
    with pytest.raises(DataValidationError) as exc_info:
        exclude_subjects_by_missing_data(df)
    
    assert "empty or None" in str(exc_info.value)
    assert exc_info.value.code == "ERR_EMPTY_PARTICIPANTS"

def test_exclude_subjects_by_missing_data_no_subject_col():
    """Test when no subject ID column is found."""
    data = {
        'name': ['Alice', 'Bob'],
        'musical_genre': [5, 3]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(DataValidationError) as exc_info:
        exclude_subjects_by_missing_data(df)
    
    assert "subject ID column" in str(exc_info.value)
    assert exc_info.value.code == "ERR_NO_SUBJECT_COL"

def test_check_data_integrity_valid_data(sample_participants):
    """Test data integrity check with valid data."""
    is_valid, message = check_data_integrity(
        sample_participants,
        dataset_id='ds000030',
        min_sample_size=5
    )
    
    assert is_valid
    assert "passed" in message.lower()

def test_check_data_integrity_underpowered():
    """Test data integrity check with insufficient sample size."""
    data = {
        'participant_id': ['sub-01', 'sub-02'],
        'musical_genre': [5, 3]
    }
    df = pd.DataFrame(data)
    
    is_valid, message = check_data_integrity(
        df,
        dataset_id='ds000030',
        min_sample_size=85
    )
    
    assert not is_valid
    assert "ERR_UNDERPOWERED" in message

def test_check_data_integrity_missing_behavioral():
    """Test data integrity check with missing behavioral variables."""
    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03'],
        'age': [25, 30, 35]
    }
    df = pd.DataFrame(data)
    
    is_valid, message = check_data_integrity(
        df,
        dataset_id='ds000030',
        min_sample_size=2
    )
    
    assert not is_valid
    assert "ERR_DATA_MISSING" in message
    assert "musical_genre" in message or "STOMP-R" in message

def test_exclude_subjects_threshold_boundary():
    """Test threshold boundary conditions."""
    # Create data where one subject has exactly 10% missing (should pass)
    # and another has 11% missing (should fail)
    data = {
        'participant_id': ['sub-01', 'sub-02'],
        'col1': [1, np.nan],
        'col2': [2, 3],
        'col3': [3, 4],
        'col4': [4, 5],
        'col5': [5, 6],
        'col6': [6, 7],
        'col7': [7, 8],
        'col8': [8, 9],
        'col9': [9, 10],
        'col10': [10, 11]
    }
    df = pd.DataFrame(data)
    
    # sub-02 has 1/10 = 10% missing (should pass with threshold=0.10)
    filtered_df, excluded_ids, _ = exclude_subjects_by_missing_data(
        df,
        missing_threshold=0.10
    )
    
    assert 'sub-02' not in excluded_ids
    assert len(filtered_df) == 2

def test_exclude_subjects_exceeds_threshold():
    """Test when missing data exceeds threshold."""
    # Create data with 20% missing (2 out of 10 columns)
    data = {
        'participant_id': ['sub-01', 'sub-02'],
        'col1': [1, np.nan],
        'col2': [2, np.nan],
        'col3': [3, 4],
        'col4': [4, 5],
        'col5': [5, 6],
        'col6': [6, 7],
        'col7': [7, 8],
        'col8': [8, 9],
        'col9': [9, 10],
        'col10': [10, 11]
    }
    df = pd.DataFrame(data)
    
    # sub-02 has 2/10 = 20% missing (should fail with threshold=0.10)
    filtered_df, excluded_ids, _ = exclude_subjects_by_missing_data(
        df,
        missing_threshold=0.10
    )
    
    assert 'sub-02' in excluded_ids
    assert len(filtered_df) == 1
    assert 'sub-01' in filtered_df['participant_id'].values
