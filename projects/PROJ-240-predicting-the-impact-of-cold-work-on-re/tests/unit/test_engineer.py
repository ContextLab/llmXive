"""
Unit tests for feature engineering module (T018).

Tests interaction feature calculation, temperature feature inclusion,
and dataset size validation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.engineer import (
    calculate_interaction_features,
    ensure_temperature_feature,
    validate_dataset_size,
    run_engineering_pipeline
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    data = {
        'cold_work': [10, 20, 30, 40, 50],
        'Mn_content': [0.5, 0.6, 0.7, 0.8, 0.9],
        'Mg_content': [0.2, 0.3, 0.4, 0.5, 0.6],
        'Si_content': [0.1, 0.2, 0.3, 0.4, 0.5],
        'Cu_content': [0.05, 0.1, 0.15, 0.2, 0.25],
        'annealing_temperature': [200, 250, 300, 350, 400],
        'time_to_peak': [100, 90, 80, 70, 60]
    }
    return pd.DataFrame(data)


def test_calculate_interaction_features(sample_dataframe):
    """Test that interaction features are correctly calculated."""
    df = calculate_interaction_features(sample_dataframe)
    
    # Check that new columns exist
    expected_interactions = [
        'cold_work_Mn_interaction',
        'cold_work_Mg_interaction',
        'cold_work_Si_interaction',
        'cold_work_Cu_interaction'
    ]
    
    for col in expected_interactions:
        assert col in df.columns, f"Missing interaction column: {col}"
    
    # Verify calculation for first row
    assert df.loc[0, 'cold_work_Mn_interaction'] == 10 * 0.5
    assert df.loc[0, 'cold_work_Mg_interaction'] == 10 * 0.2
    assert df.loc[0, 'cold_work_Si_interaction'] == 10 * 0.1
    assert df.loc[0, 'cold_work_Cu_interaction'] == 10 * 0.05
    
    # Verify calculation for last row
    assert df.loc[4, 'cold_work_Mn_interaction'] == 50 * 0.9
    assert df.loc[4, 'cold_work_Mg_interaction'] == 50 * 0.6
    assert df.loc[4, 'cold_work_Si_interaction'] == 50 * 0.5
    assert df.loc[4, 'cold_work_Cu_interaction'] == 50 * 0.25


def test_ensure_temperature_feature(sample_dataframe):
    """Test that annealing temperature is properly included."""
    df = ensure_temperature_feature(sample_dataframe)
    
    assert 'annealing_temperature' in df.columns
    assert df['annealing_temperature'].dtype in ['int64', 'float64']
    
    # Verify values are preserved
    assert list(df['annealing_temperature']) == [200, 250, 300, 350, 400]


def test_ensure_temperature_feature_missing_column():
    """Test that error is raised when temperature column is missing."""
    data = {
        'cold_work': [10, 20, 30],
        'Mn_content': [0.5, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Required column 'annealing_temperature' not found"):
        ensure_temperature_feature(df)


def test_validate_dataset_size_pass(sample_dataframe):
    """Test that validation passes with sufficient rows."""
    # Should not raise
    validate_dataset_size(sample_dataframe, min_rows=50)
    
    # Create a larger dataframe
    large_df = pd.concat([sample_dataframe] * 10, ignore_index=True)
    validate_dataset_size(large_df, min_rows=500)


def test_validate_dataset_size_fail():
    """Test that validation fails with insufficient rows."""
    data = {
        'cold_work': [10, 20, 30],
        'Mn_content': [0.5, 0.6, 0.7],
        'Mg_content': [0.2, 0.3, 0.4],
        'Si_content': [0.1, 0.2, 0.3],
        'Cu_content': [0.05, 0.1, 0.15],
        'annealing_temperature': [200, 250, 300],
        'time_to_peak': [100, 90, 80]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError, match="Dataset size validation failed"):
        validate_dataset_size(df, min_rows=50)


def test_calculate_interaction_features_missing_column(sample_dataframe):
    """Test behavior when a composition column is missing."""
    # Remove one composition column
    df_missing = sample_dataframe.drop(columns=['Cu_content'])
    
    # Should not raise, but should skip the missing interaction
    result = calculate_interaction_features(df_missing)
    
    # Check that Cu interaction is not created
    assert 'cold_work_Cu_interaction' not in result.columns
    
    # Check that other interactions are still created
    assert 'cold_work_Mn_interaction' in result.columns
    assert 'cold_work_Mg_interaction' in result.columns
    assert 'cold_work_Si_interaction' in result.columns