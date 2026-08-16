"""
Tests for behavioral validation and missing score handling (T017).
"""
import os
import tempfile
import pandas as pd
import pytest

from code.data.behavioral_validator import (
    identify_missing_scores,
    log_missing_score_exclusions,
    filter_missing_scores,
    run_behavioral_validation_pipeline
)
from code.utils.logging import get_exclusion_log_path

@pytest.fixture
def sample_merged_df():
    """Create a sample merged DataFrame for testing."""
    data = {
        'Subject_ID': ['1001', '1002', '1003', '1004', '1005'],
        'Mean_FD': [0.1, 0.15, 0.25, 0.12, 0.18],
        'Age': [22, 25, 30, 28, 35],
        'Sex': ['M', 'F', 'M', 'F', 'M'],
        'Flexibility_Score': [0.85, None, 0.92, '', 0.78]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_exclusion_log():
    """Create a temporary file for exclusion log testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("Subject_ID,Exclusion_Reason,Mean_FD\n")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_identify_missing_scores_with_nulls(sample_merged_df):
    """Test identification of subjects with null or empty scores."""
    missing = identify_missing_scores(sample_merged_df, 'Flexibility_Score')
    assert len(missing) == 2
    assert '1002' in missing
    assert '1004' in missing

def test_identify_missing_scores_all_valid():
    """Test identification when all scores are valid."""
    data = {
        'Subject_ID': ['1001', '1002'],
        'Flexibility_Score': [0.85, 0.92]
    }
    df = pd.DataFrame(data)
    missing = identify_missing_scores(df, 'Flexibility_Score')
    assert len(missing) == 0

def test_filter_missing_scores_removes_correct_rows(sample_merged_df):
    """Test that filter removes subjects with missing scores."""
    filtered_df = filter_missing_scores(sample_merged_df, 'Flexibility_Score')
    assert len(filtered_df) == 3
    assert '1002' not in filtered_df['Subject_ID'].values
    assert '1004' not in filtered_df['Subject_ID'].values
    assert '1001' in filtered_df['Subject_ID'].values
    assert '1003' in filtered_df['Subject_ID'].values
    assert '1005' in filtered_df['Subject_ID'].values

def test_log_missing_score_exclusions_creates_rows(temp_exclusion_log):
    """Test that logging creates correct rows in exclusion log."""
    missing_subjects = ['1002', '1004']
    log_missing_score_exclusions(missing_subjects, temp_exclusion_log)
    
    df = pd.read_csv(temp_exclusion_log)
    assert len(df) == 2
    assert all(df['Exclusion_Reason'] == 'Missing_Behavioral_Score')
    assert '1002' in df['Subject_ID'].values
    assert '1004' in df['Subject_ID'].values
    assert all(df['Mean_FD'] == 'N/A')

def test_run_behavioral_validation_pipeline(sample_merged_df, temp_exclusion_log):
    """Test the complete validation pipeline."""
    result = run_behavioral_validation_pipeline(
        sample_merged_df, 
        'Flexibility_Score',
        temp_exclusion_log
    )
    
    # Check result
    assert len(result) == 3
    assert '1002' not in result['Subject_ID'].values
    
    # Check log file
    log_df = pd.read_csv(temp_exclusion_log)
    assert len(log_df) == 2
    assert all(log_df['Exclusion_Reason'] == 'Missing_Behavioral_Score')