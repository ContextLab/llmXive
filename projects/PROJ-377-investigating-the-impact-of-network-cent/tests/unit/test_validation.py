"""
Unit tests for the validation module (T015).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from data.validation import validate_retention_and_behavioral_data
from utils.config import Config, reset_config

@pytest.fixture
def sample_behavioral_df():
    """Create a sample DataFrame with valid behavioral data."""
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(1, 101)],
        'pre_score': np.random.uniform(10, 50, 100),
        'post_score': np.random.uniform(10, 50, 100),
        'improvement': np.random.uniform(-5, 20, 100),
        'age': np.random.randint(18, 80, 100),
        'sex': np.random.choice(['M', 'F'], 100)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_behavioral_df_missing():
    """Create a DataFrame with missing critical behavioral data."""
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(1, 11)],
        'pre_score': np.random.uniform(10, 50, 10),
        'post_score': np.random.uniform(10, 50, 10),
        'improvement': [np.nan] + [np.random.uniform(-5, 20, 9)].tolist(), # One missing
        'age': np.random.randint(18, 80, 10),
        'sex': np.random.choice(['M', 'F'], 10)
    }
    return pd.DataFrame(data)

@pytest.fixture
def empty_df():
    return pd.DataFrame(columns=['subject_id', 'improvement'])

def test_valid_retention(sample_behavioral_df):
    """Test that valid data passes retention check."""
    # 100 subjects, expect 100. Rate = 1.0. Threshold = 0.8. Should pass.
    is_valid, msg, _ = validate_retention_and_behavioral_data(
        sample_behavioral_df, 
        min_retention_rate=0.80, 
        total_subjects_expected=100
    )
    assert is_valid is True
    assert "Validation passed" in msg

def test_low_retention_raises(sample_behavioral_df):
    """Test that low retention rate raises RuntimeError."""
    # 100 subjects, but we only kept 50. Rate = 0.5. Threshold = 0.8. Should fail.
    with pytest.raises(RuntimeError) as excinfo:
        validate_retention_and_behavioral_data(
            sample_behavioral_df, 
            min_retention_rate=0.80, 
            total_subjects_expected=200 # Expecting 200, have 100 -> 50% retention
        )
    assert "below the required threshold" in str(excinfo.value)

def test_missing_behavioral_data_raises(sample_behavioral_df_missing):
    """Test that missing behavioral data raises RuntimeError."""
    with pytest.raises(RuntimeError) as excinfo:
        validate_retention_and_behavioral_data(
            sample_behavioral_df_missing,
            min_retention_rate=0.80,
            total_subjects_expected=10
        )
    assert "Behavioral data missing" in str(excinfo.value)

def test_empty_dataframe_raises(empty_df):
    """Test that an empty DataFrame raises RuntimeError."""
    with pytest.raises(RuntimeError) as excinfo:
        validate_retention_and_behavioral_data(
            empty_df,
            min_retention_rate=0.80,
            total_subjects_expected=100
        )
    assert "empty" in str(excinfo.value)

def test_retention_calculation():
    """Test retention rate calculation logic."""
    df = pd.DataFrame({
        'subject_id': ['s1', 's2', 's3'],
        'improvement': [1.0, 2.0, 3.0]
    })
    # 3 retained, 4 expected -> 75%
    is_valid, _, _ = validate_retention_and_behavioral_data(
        df, 
        min_retention_rate=0.70, 
        total_subjects_expected=4
    )
    assert is_valid is True # 0.75 >= 0.70

    # 3 retained, 5 expected -> 60%
    with pytest.raises(RuntimeError):
        validate_retention_and_behavioral_data(
            df, 
            min_retention_rate=0.70, 
            total_subjects_expected=5
        )
