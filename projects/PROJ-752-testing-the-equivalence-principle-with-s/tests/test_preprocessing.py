import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data.preprocessing import (
    filter_residuals,
    handle_sparse_satellites,
    align_time_series,
    merge_multi_satellite_datasets,
    preprocess_slr_data
)
from utils.logging import AnalysisError

@pytest.fixture
def sample_data():
    """Create sample SLR data for testing."""
    n_points = 1000
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="1min")
    residuals = np.random.normal(0, 0.015, n_points)  # Mean 0, std 1.5cm
    
    return pd.DataFrame({
        "time": dates,
        "satellite_id": "LAGEOS-1",
        "range": 12000000.0 + np.random.normal(0, 0.01, n_points),
        "residual": residuals
    })

@pytest.fixture
def outlier_data():
    """Create data with outliers > 2cm."""
    n_points = 1000
    dates = pd.date_range(start="2023-01-01", periods=n_points, freq="1min")
    residuals = np.random.normal(0, 0.01, n_points)
    # Inject outliers
    residuals[100:150] = np.random.uniform(0.025, 0.05, 50)  # 2.5-5cm
    
    return pd.DataFrame({
        "time": dates,
        "satellite_id": "LAGEOS-1",
        "range": 12000000.0 + residuals,
        "residual": residuals
    })

@pytest.fixture
def multi_sat_data():
    """Create data for multiple satellites."""
    sat1 = pd.DataFrame({
        "time": pd.date_range("2023-01-01", periods=500, freq="1min"),
        "satellite_id": "LAGEOS-1",
        "range": 12000000.0,
        "residual": np.random.normal(0, 0.01, 500)
    })
    
    sat2 = pd.DataFrame({
        "time": pd.date_range("2023-01-01 02:00:00", periods=500, freq="1min"),
        "satellite_id": "ETALON-1",
        "range": 10000000.0,
        "residual": np.random.normal(0, 0.01, 500)
    })
    
    return [sat1, sat2]

def test_filter_residuals_basic(sample_data):
    """Test basic residual filtering."""
    filtered = filter_residuals(sample_data, threshold_m=0.02)
    
    # Check that all residuals are within threshold
    assert all(np.abs(filtered["residual"]) <= 0.02)
    # Check that we didn't add new rows
    assert len(filtered) <= len(sample_data)

def test_filter_residuals_outliers(outlier_data):
    """Test that outliers > 2cm are removed."""
    initial_count = len(outlier_data)
    filtered = filter_residuals(outlier_data, threshold_m=0.02)
    
    # Should have removed the injected outliers
    assert len(filtered) < initial_count
    assert all(np.abs(filtered["residual"]) <= 0.02)

def test_filter_residuals_missing_column(sample_data):
    """Test error when residual column is missing."""
    df = sample_data.drop(columns=["residual"])
    with pytest.raises(AnalysisError):
        filter_residuals(df, residual_col="nonexistent")

def test_handle_sparse_satellites_warns():
    """Test that sparse satellites trigger a warning."""
    # Create data with < 500 points
    sparse_df = pd.DataFrame({
        "time": pd.date_range("2023-01-01", periods=100, freq="1min"),
        "satellite_id": "SPARSE-SAT",
        "residual": np.random.normal(0, 0.01, 100)
    })
    
    # This should log a warning but not raise
    result = handle_sparse_satellites(sparse_df, min_points=500)
    assert len(result) == 100  # Data is returned, just warned

def test_handle_sparse_satellites_enough_points():
    """Test that sufficient points pass without issue."""
    sufficient_df = pd.DataFrame({
        "time": pd.date_range("2023-01-01", periods=600, freq="1min"),
        "satellite_id": "GOOD-SAT",
        "residual": np.random.normal(0, 0.01, 600)
    })
    
    result = handle_sparse_satellites(sufficient_df, min_points=500)
    assert len(result) == 600

def test_align_time_series(sample_data):
    """Test time series alignment."""
    # Introduce gaps
    sample_data = sample_data.iloc[::2].reset_index(drop=True)  # Keep every other row
    
    aligned = align_time_series(sample_data, frequency="2min", method="nearest")
    
    # Check that time is regular
    time_diffs = aligned["time"].diff().dropna()
    assert all(time_diffs == pd.Timedelta("2min"))

def test_merge_multi_satellite_datasets(multi_sat_data):
    """Test merging multiple satellite datasets."""
    merged = merge_multi_satellite_datasets(
        multi_sat_data,
        time_col="time",
        satellite_col="satellite_id",
        common_time_range=False
    )
    
    assert len(merged) == 1000
    assert "satellite_id" in merged.columns
    assert len(merged["satellite_id"].unique()) == 2

def test_merge_multi_satellite_common_range(multi_sat_data):
    """Test merging with common time range."""
    # Sat1: 00:00-08:20, Sat2: 02:00-10:20
    # Common: 02:00-08:20
    merged = merge_multi_satellite_datasets(
        multi_sat_data,
        time_col="time",
        satellite_col="satellite_id",
        common_time_range=True
    )
    
    # Should only have overlapping points
    assert len(merged) < 1000
    assert len(merged) > 0

def test_merge_no_overlap():
    """Test error when no time overlap exists."""
    sat1 = pd.DataFrame({
        "time": pd.date_range("2023-01-01", periods=100, freq="1min"),
        "satellite_id": "SAT1",
        "residual": [0.01] * 100
    })
    sat2 = pd.DataFrame({
        "time": pd.date_range("2023-01-02", periods=100, freq="1min"),  # Next day
        "satellite_id": "SAT2",
        "residual": [0.01] * 100
    })
    
    with pytest.raises(AnalysisError, match="No overlapping time range"):
        merge_multi_satellite_datasets([sat1, sat2], common_time_range=True)

def test_preprocess_slr_data_full_pipeline():
    """Test the full preprocessing pipeline."""
    # Create two satellites with some outliers
    sat1 = pd.DataFrame({
        "time": pd.date_range("2023-01-01", periods=600, freq="1min"),
        "satellite_id": "LAGEOS-1",
        "range": 12000000.0,
        "residual": np.concatenate([
            np.random.normal(0, 0.01, 550),
            np.random.uniform(0.025, 0.05, 50)  # Outliers
        ])
    })
    
    sat2 = pd.DataFrame({
        "time": pd.date_range("2023-01-01 01:00:00", periods=600, freq="1min"),
        "satellite_id": "ETALON-1",
        "range": 10000000.0,
        "residual": np.random.normal(0, 0.01, 600)
    })
    
    result = preprocess_slr_data(
        [sat1, sat2],
        residual_threshold_m=0.02,
        min_points_per_sat=500,
        align_to_common=True
    )
    
    # Check results
    assert len(result) > 0
    assert all(np.abs(result["residual"]) <= 0.02)
    assert len(result["satellite_id"].unique()) == 2
    assert "time" in result.columns

def test_preprocess_empty_input():
    """Test error on empty input."""
    with pytest.raises(AnalysisError, match="No raw data provided"):
        preprocess_slr_data([])

def test_preprocess_empty_result():
    """Test error when filtering removes all data."""
    # All outliers
    sat = pd.DataFrame({
        "time": pd.date_range("2023-01-01", periods=100, freq="1min"),
        "satellite_id": "SAT1",
        "range": 12000000.0,
        "residual": [0.05] * 100  # All > 2cm
    })
    
    with pytest.raises(AnalysisError, match="empty dataset"):
        preprocess_slr_data([sat], residual_threshold_m=0.02)