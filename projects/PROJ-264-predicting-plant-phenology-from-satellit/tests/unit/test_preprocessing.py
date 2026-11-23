"""
Unit tests for the preprocessing module.

These tests verify the correctness of lagged feature creation and
multicollinearity exclusion logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.data.preprocessing import create_lagged_features, exclude_gdd_cumulative, run_preprocessing

@pytest.fixture
def sample_data():
    """Create a sample DataFrame with time-series data for multiple sites."""
    data = {
        'site_id': ['A', 'A', 'A', 'A', 'A', 'B', 'B', 'B', 'B', 'B'],
        'date': pd.date_range('2020-01-01', periods=5, freq='M').tolist() * 2,
        'temp_mean': [10, 12, 15, 18, 20, 8, 10, 13, 16, 19],
        'precip': [50, 45, 40, 35, 30, 60, 55, 50, 45, 40],
        'ndvi': [0.2, 0.3, 0.5, 0.7, 0.8, 0.15, 0.25, 0.45, 0.65, 0.85],
        'phenology_event_day': [None, None, None, 120, 125, None, None, None, 115, 120],
        'gdd_cumulative': [10, 25, 50, 80, 110, 8, 22, 48, 78, 108]
    }
    return pd.DataFrame(data)

def test_create_lagged_features_basic(sample_data):
    """Test basic creation of lagged features."""
    feature_cols = ['temp_mean', 'precip', 'ndvi']

    result = create_lagged_features(
        sample_data,
        feature_columns=feature_cols,
        time_column='date',
        site_column='site_id',
        lag_window_size=2,
        target_offset=1
    )

    # Check that lagged columns are created
    expected_lag_cols = [
        'temp_mean_lag_1', 'temp_mean_lag_2',
        'precip_lag_1', 'precip_lag_2',
        'ndvi_lag_1', 'ndvi_lag_2'
    ]

    for col in expected_lag_cols:
        assert col in result.columns, f"Expected column {col} not found in result"

    # Check that rows with insufficient history are dropped
    # Site A has 5 rows, with lag_window_size=2, we lose the first 2 rows
    # Site B has 5 rows, we lose the first 2 rows
    # We also lose rows where target is NaN (last row for each site due to target_offset=1)
    # So we expect 3 rows per site = 6 rows total
    assert len(result) == 6, f"Expected 6 rows, got {len(result)}"

def test_create_lagged_features_empty_input():
    """Test that empty input returns empty output."""
    empty_df = pd.DataFrame(columns=['site_id', 'date', 'temp_mean'])
    result = create_lagged_features(empty_df, ['temp_mean'])
    assert result.empty

def test_create_lagged_features_per_site():
    """Test that lagging is done independently per site."""
    data = {
        'site_id': ['A', 'A', 'A', 'B', 'B', 'B'],
        'date': pd.date_range('2020-01-01', periods=3, freq='M').tolist() * 2,
        'temp_mean': [10, 12, 15, 20, 22, 25]
    }
    df = pd.DataFrame(data)

    result = create_lagged_features(
        df,
        feature_columns=['temp_mean'],
        time_column='date',
        site_column='site_id',
        lag_window_size=1,
        target_offset=1
    )

    # Site A: lag_1 for row 1 should be 10, for row 2 should be 12
    # Site B: lag_1 for row 4 should be 20, for row 5 should be 22
    site_a = result[result['site_id'] == 'A']
    site_b = result[result['site_id'] == 'B']

    assert site_a['temp_mean_lag_1'].iloc[0] == 10
    assert site_a['temp_mean_lag_1'].iloc[1] == 12
    assert site_b['temp_mean_lag_1'].iloc[0] == 20
    assert site_b['temp_mean_lag_1'].iloc[1] == 22

def test_exclude_gdd_cumulative_present(sample_data):
    """Test that gdd_cumulative is removed when present."""
    assert 'gdd_cumulative' in sample_data.columns

    result = exclude_gdd_cumulative(sample_data)

    assert 'gdd_cumulative' not in result.columns
    assert len(result.columns) == len(sample_data.columns) - 1

def test_exclude_gdd_cumulative_absent():
    """Test that function handles missing gdd_cumulative gracefully."""
    data = {
        'site_id': ['A', 'A'],
        'date': pd.date_range('2020-01-01', periods=2, freq='M'),
        'temp_mean': [10, 12]
    }
    df = pd.DataFrame(data)

    result = exclude_gdd_cumulative(df)

    assert 'gdd_cumulative' not in result.columns
    assert len(result.columns) == len(df.columns)

def test_run_preprocessing(tmp_path):
    """Test the full preprocessing pipeline with real file I/O."""
    # Create sample input data
    input_data = {
        'site_id': ['A', 'A', 'A', 'A', 'A'],
        'date': pd.date_range('2020-01-01', periods=5, freq='M'),
        'temp_mean': [10, 12, 15, 18, 20],
        'precip': [50, 45, 40, 35, 30],
        'ndvi': [0.2, 0.3, 0.5, 0.7, 0.8],
        'phenology_event_day': [None, None, None, 120, 125],
        'gdd_cumulative': [10, 25, 50, 80, 110]
    }
    input_df = pd.DataFrame(input_data)

    input_path = tmp_path / "aligned_dataset.csv"
    output_path = tmp_path / "lagged_features_dataset.csv"

    input_df.to_csv(input_path, index=False)

    # Run preprocessing
    result_path = run_preprocessing(
        input_path=input_path,
        output_path=output_path
    )

    # Verify output file exists
    assert result_path.exists()

    # Load and verify content
    result_df = pd.read_csv(result_path)

    # Check for lagged columns
    assert 'temp_mean_lag_1' in result_df.columns
    assert 'temp_mean_lag_2' in result_df.columns
    assert 'gdd_cumulative' not in result_df.columns

    # Check row count (5 original - 2 for lag - 1 for target = 2 rows)
    assert len(result_df) == 2