"""
Tests for data preprocessing functions.
"""
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
def sample_slr_data():
    """Create sample SLR normal point data for testing."""
    times = [datetime(2023, 1, 1, i, 0, 0) for i in range(24)]
    data = {
        "time": times * 2,
        "satellite_id": ["LAGEOS-1"] * 24 + ["LAGEOS-2"] * 24,
        "residual": [0.01] * 10 + [0.03] * 10 + [0.01] * 4 + [0.01] * 24,
        "range": [8000000.0 + i * 0.1 for i in range(48)]
    }
    return pd.DataFrame(data)


def test_filter_residuals_removes_large_values(sample_slr_data):
    """Test that filter_residuals removes points with residuals > 2cm."""
    filtered = filter_residuals(sample_slr_data, residual_col="residual", threshold_m=0.02)

    assert len(filtered) < len(sample_slr_data)
    assert all(abs(filtered["residual"]) <= 0.02)


def test_filter_residuals_missing_column():
    """Test that filter_residuals raises error for missing column."""
    df = pd.DataFrame({"time": [datetime.now()]})
    with pytest.raises(AnalysisError):
        filter_residuals(df, residual_col="nonexistent")


def test_handle_sparse_satellites_removes_small_datasets():
    """Test that handle_sparse_satellites removes satellites with < 500 points."""
    times = [datetime(2023, 1, 1, i, 0, 0) for i in range(100)]
    data = {
        "time": times,
        "satellite_id": ["SPARSE-SAT"] * 100,
        "residual": [0.01] * 100
    }
    df = pd.DataFrame(data)

    filtered_df, removed = handle_sparse_satellites(df, min_points=500)

    assert len(filtered_df) == 0
    assert "SPARSE-SAT" in removed


def test_handle_sparse_satellites_keeps_large_datasets():
    """Test that handle_sparse_satellites keeps satellites with >= 500 points."""
    times = [datetime(2023, 1, 1, i, 0, 0) for i in range(600)]
    data = {
        "time": times,
        "satellite_id": ["RICH-SAT"] * 600,
        "residual": [0.01] * 600
    }
    df = pd.DataFrame(data)

    filtered_df, removed = handle_sparse_satellites(df, min_points=500)

    assert len(filtered_df) == 600
    assert len(removed) == 0


def test_align_time_series_resamples_correctly():
    """Test that align_time_series resamples to target frequency."""
    # Create data with irregular timestamps (every 30 minutes)
    times = [datetime(2023, 1, 1, 0, i * 30, 0) for i in range(48)]
    data = {
        "time": times,
        "satellite_id": ["TEST-SAT"] * 48,
        "value": list(range(48))
    }
    df = pd.DataFrame(data)

    aligned = align_time_series(df, target_frequency="1H")

    # Should have 24 hourly points instead of 48 half-hourly points
    assert len(aligned) == 24
    assert aligned["satellite_id"].iloc[0] == "TEST-SAT"


def test_merge_multi_satellite_datasets():
    """Test merging of multiple satellite datasets."""
    # Create two satellite datasets
    times1 = [datetime(2023, 1, 1, i, 0, 0) for i in range(10)]
    times2 = [datetime(2023, 1, 1, i, 0, 0) for i in range(10)]

    df1 = pd.DataFrame({
        "time": times1,
        "satellite_id": ["SAT-1"] * 10,
        "value": list(range(10))
    })

    df2 = pd.DataFrame({
        "time": times2,
        "satellite_id": ["SAT-2"] * 10,
        "value": list(range(10, 20))
    })

    merged = merge_multi_satellite_datasets([df1, df2], target_frequency="1H")

    assert len(merged) == 20
    assert set(merged["satellite_id"].unique()) == {"SAT-1", "SAT-2"}


def test_preprocess_slr_data_full_pipeline(sample_slr_data):
    """Test the complete preprocessing pipeline."""
    processed = preprocess_slr_data(
        sample_slr_data,
        residual_threshold_m=0.02,
        min_points_per_sat=500
    )

    # Should filter out large residuals and sparse satellites
    assert len(processed) < len(sample_slr_data)
    assert all(abs(processed["residual"]) <= 0.02)
    assert "time" in processed.columns
    assert "satellite_id" in processed.columns