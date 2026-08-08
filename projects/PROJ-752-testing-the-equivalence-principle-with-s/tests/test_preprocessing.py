"""
Tests for the preprocessing module.

These tests verify the correctness of residual filtering, sparse satellite handling,
time alignment, and multi-satellite merging operations.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocessing import (
    filter_residuals,
    handle_sparse_satellites,
    align_time_series,
    merge_multi_satellite_datasets,
    preprocess_slr_data,
    RESIDUAL_THRESHOLD_CM,
    MIN_POINTS_PER_SATELLITE
)
from utils.logging import AnalysisError


@pytest.fixture
def sample_slr_data():
    """Create sample SLR data for testing."""
    np.random.seed(42)
    n_points = 1000

    # Generate timestamps
    base_time = datetime(2023, 1, 1)
    times = [base_time + timedelta(hours=i) for i in range(n_points)]

    # Generate residuals with some outliers
    residuals = np.random.normal(0, 0.01, n_points)  # 1cm std dev
    # Add some outliers > 2cm
    outliers = np.random.choice(n_points, 50, replace=False)
    residuals[outliers] = np.random.uniform(0.025, 0.05, 50)  # 2.5-5cm outliers

    # Create satellite assignments
    satellites = np.random.choice(['LAGEOS-1', 'LAGEOS-2', 'Etalon-1', 'Etalon-2', 'Starlette'], n_points)

    df = pd.DataFrame({
        'time': times,
        'satellite_id': satellites,
        'residual_m': residuals,
        'range_m': np.random.uniform(5000000, 6000000, n_points),
        'station_id': np.random.choice(['1234', '5678', '9012'], n_points)
    })

    return df


@pytest.fixture
def sparse_satellite_data():
    """Create data with one satellite having insufficient points."""
    np.random.seed(123)

    # LAGEOS-1 with many points
    lageos_points = 500
    lageos_df = pd.DataFrame({
        'time': [datetime(2023, 1, 1) + timedelta(hours=i) for i in range(lageos_points)],
        'satellite_id': 'LAGEOS-1',
        'residual_m': np.random.normal(0, 0.01, lageos_points),
        'range_m': np.random.uniform(5000000, 6000000, lageos_points)
    })

    # Etalon-1 with few points (below threshold)
    etalon_points = 30  # Below MIN_POINTS_PER_SATELLITE (50)
    etalon_df = pd.DataFrame({
        'time': [datetime(2023, 1, 1) + timedelta(hours=i) for i in range(etalon_points)],
        'satellite_id': 'Etalon-1',
        'residual_m': np.random.normal(0, 0.01, etalon_points),
        'range_m': np.random.uniform(5000000, 6000000, etalon_points)
    })

    return pd.concat([lageos_df, etalon_df], ignore_index=True)


def test_filter_residuals_removes_outliers(sample_slr_data):
    """Test that filter_residuals correctly removes points with |residual| > 2cm."""
    initial_count = len(sample_slr_data)

    # Count outliers manually
    outliers_before = (np.abs(sample_slr_data['residual_m']) > 0.02).sum()

    filtered_df = filter_residuals(sample_slr_data, 'residual_m', threshold_cm=2.0)

    # Verify no outliers remain
    outliers_after = (np.abs(filtered_df['residual_m']) > 0.02).sum()
    assert outliers_after == 0, f"Outliers remain after filtering: {outliers_after}"

    # Verify correct number of points removed
    assert len(filtered_df) == initial_count - outliers_before

    # Verify all remaining points are within threshold
    assert all(np.abs(filtered_df['residual_m']) <= 0.02)


def test_filter_residuals_handles_nan():
    """Test that filter_residuals removes rows with NaN residuals."""
    df = pd.DataFrame({
        'time': [datetime(2023, 1, 1), datetime(2023, 1, 2), datetime(2023, 1, 3)],
        'satellite_id': ['LAGEOS-1', 'LAGEOS-1', 'LAGEOS-1'],
        'residual_m': [0.01, np.nan, 0.005]
    })

    filtered_df = filter_residuals(df, 'residual_m')

    assert len(filtered_df) == 2
    assert not filtered_df['residual_m'].isna().any()


def test_filter_residuals_missing_column(sample_slr_data):
    """Test that filter_residuals raises error for missing residual column."""
    with pytest.raises(AnalysisError):
        filter_residuals(sample_slr_data, 'nonexistent_column')


def test_handle_sparse_satellites_excludes_insufficient(sparse_satellite_data):
    """Test that handle_sparse_satellites excludes satellites with < min_points."""
    filtered_df, excluded_sats = handle_sparse_satellites(
        sparse_satellite_data,
        satellite_column='satellite_id',
        min_points=MIN_POINTS_PER_SATELLITE
    )

    # Verify Etalon-1 was excluded
    assert 'Etalon-1' in excluded_sats
    assert 'Etalon-1' not in filtered_df['satellite_id'].values

    # Verify LAGEOS-1 was kept
    assert 'LAGEOS-1' in filtered_df['satellite_id'].values

    # Verify all remaining satellites have >= min_points
    counts = filtered_df['satellite_id'].value_counts()
    assert all(counts >= MIN_POINTS_PER_SATELLITE)


def test_handle_sparse_satellites_all_excluded():
    """Test that error is raised when all satellites have insufficient data."""
    df = pd.DataFrame({
        'time': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
        'satellite_id': ['Sat-A', 'Sat-B'],
        'residual_m': [0.01, 0.02]
    })

    with pytest.raises(AnalysisError) as exc_info:
        handle_sparse_satellites(df, min_points=MIN_POINTS_PER_SATELLITE)

    assert "All satellites have fewer than" in str(exc_info.value)


def test_handle_sparse_satellites_missing_column(sample_slr_data):
    """Test that handle_sparse_satellites raises error for missing satellite column."""
    with pytest.raises(AnalysisError):
        handle_sparse_satellites(sample_slr_data, satellite_column='nonexistent')


def test_align_time_series_resamples_correctly():
    """Test that align_time_series correctly resamples to regular frequency."""
    # Create data with irregular timestamps
    df = pd.DataFrame({
        'time': [
            datetime(2023, 1, 1, 0, 0),
            datetime(2023, 1, 1, 0, 30),  # 30 min later
            datetime(2023, 1, 1, 1, 0),
            datetime(2023, 1, 1, 1, 45),  # 45 min later
            datetime(2023, 1, 1, 2, 0)
        ],
        'satellite_id': ['LAGEOS-1'] * 5,
        'residual_m': [0.01, 0.02, 0.015, 0.025, 0.01]
    })

    aligned_df = align_time_series(df, time_column='time', frequency='H', satellite_column='satellite_id')

    # Should have 3 hourly bins (0:00, 1:00, 2:00)
    assert len(aligned_df) == 3

    # Verify times are on the hour
    for t in aligned_df['time']:
        assert t.minute == 0
        assert t.second == 0


def test_align_time_series_handles_nan():
    """Test that align_time_series drops empty bins."""
    # Create data with large gaps
    df = pd.DataFrame({
        'time': [
            datetime(2023, 1, 1, 0, 0),
            datetime(2023, 1, 1, 5, 0)  # 5 hours later, skipping 1-4
        ],
        'satellite_id': ['LAGEOS-1'] * 2,
        'residual_m': [0.01, 0.02]
    })

    aligned_df = align_time_series(df, time_column='time', frequency='H', satellite_column='satellite_id')

    # Should only have 2 rows (no empty bins)
    assert len(aligned_df) == 2


def test_align_time_series_missing_column(sample_slr_data):
    """Test that align_time_series raises error for missing time column."""
    with pytest.raises(AnalysisError):
        align_time_series(sample_slr_data, time_column='nonexistent')


def test_merge_multi_satellite_datasets():
    """Test merging multiple satellite DataFrames."""
    df1 = pd.DataFrame({
        'time': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
        'satellite_id': ['LAGEOS-1', 'LAGEOS-1'],
        'residual_m': [0.01, 0.02]
    })

    df2 = pd.DataFrame({
        'time': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
        'satellite_id': ['Etalon-1', 'Etalon-1'],
        'residual_m': [0.015, 0.025]
    })

    merged = merge_multi_satellite_datasets([df1, df2])

    assert len(merged) == 4
    assert set(merged['satellite_id'].unique()) == {'LAGEOS-1', 'Etalon-1'}


def test_merge_multi_satellite_datasets_empty_list():
    """Test that merge_multi_satellite_datasets raises error for empty list."""
    with pytest.raises(AnalysisError):
        merge_multi_satellite_datasets([])


def test_merge_multi_satellite_datasets_missing_column():
    """Test that merge_multi_satellite_datasets raises error for missing columns."""
    df1 = pd.DataFrame({
        'time': [datetime(2023, 1, 1)],
        'residual_m': [0.01]  # Missing satellite_id
    })

    with pytest.raises(AnalysisError):
        merge_multi_satellite_datasets([df1])


def test_preprocess_slr_data_full_pipeline(sample_slr_data):
    """Test the complete preprocessing pipeline."""
    initial_points = len(sample_slr_data)

    processed_df, stats = preprocess_slr_data(
        sample_slr_data,
        residual_column='residual_m',
        satellite_column='satellite_id',
        time_column='time'
    )

    # Verify stats dictionary structure
    assert 'initial_points' in stats
    assert 'final_points' in stats
    assert 'filtered_by_residual' in stats
    assert 'excluded_satellites' in stats

    # Verify final points <= initial points
    assert stats['final_points'] <= stats['initial_points']

    # Verify all residuals are within threshold
    assert all(np.abs(processed_df['residual_m']) <= 0.02)

    # Verify no NaN in residuals
    assert not processed_df['residual_m'].isna().any()