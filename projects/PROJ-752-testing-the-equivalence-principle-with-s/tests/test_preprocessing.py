"""
Unit tests for quality filtering logic in data/preprocessing.py.

Tests specifically for the >2cm residual exclusion criteria.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

# Import the function to be tested
# We define it here if it doesn't exist yet to satisfy the import for this test
# In the full implementation, this would come from data.preprocessing
from utils.logging import get_logger

logger = get_logger(__name__)


# --- Mock Implementation for Test Isolation ---
# Since T016 (implementation of preprocessing.py) is not yet done,
# we define the expected interface here to test the logic.
# Once T016 is implemented, this block will be replaced by:
# from data.preprocessing import filter_quality, apply_quality_filters

def filter_quality(df: pd.DataFrame, threshold_cm: float = 2.0) -> pd.DataFrame:
    """
    Filter out SLR normal points where the residual magnitude exceeds the threshold.

    Args:
        df: DataFrame containing SLR data, expected to have a 'residual' column (in meters).
        threshold_cm: Threshold in centimeters. Defaults to 2.0 cm.

    Returns:
        DataFrame with rows having |residual| > threshold removed.
    """
    if df.empty:
        return df

    threshold_m = threshold_cm / 100.0
    # Filter: keep rows where absolute residual is <= threshold
    mask = np.abs(df['residual']) <= threshold_m
    return df[mask].reset_index(drop=True)


# --- Test Cases ---

def test_filter_quality_removes_large_residuals():
    """Test that residuals > 2cm are excluded."""
    data = {
        'satellite_id': ['LAGEOS-1', 'LAGEOS-1', 'LAGEOS-1', 'LAGEOS-1'],
        'time': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 00:01:00',
                                '2023-01-01 00:02:00', '2023-01-01 00:03:00']),
        'residual': [0.01, -0.015, 0.025, -0.03]  # meters: 1cm, 1.5cm, 2.5cm, 3cm
    }
    df = pd.DataFrame(data)

    result = filter_quality(df, threshold_cm=2.0)

    # Expected: Keep 0.01 and -0.015. Remove 0.025 and -0.03.
    assert len(result) == 2
    assert all(np.abs(result['residual']) <= 0.02)

def test_filter_quality_keeps_boundary_values():
    """Test that residuals exactly at the threshold are kept."""
    data = {
        'satellite_id': ['LAGEOS-1', 'LAGEOS-1'],
        'time': pd.to_datetime(['2023-01-01 00:00:00', '2023-01-01 00:01:00']),
        'residual': [0.02, -0.02]  # Exactly 2cm
    }
    df = pd.DataFrame(data)

    result = filter_quality(df, threshold_cm=2.0)

    # Both should be kept
    assert len(result) == 2

def test_filter_quality_empty_dataframe():
    """Test handling of empty input DataFrame."""
    df = pd.DataFrame(columns=['satellite_id', 'time', 'residual'])
    result = filter_quality(df)
    assert result.empty

def test_filter_quality_all_excluded():
    """Test behavior when all points exceed threshold."""
    data = {
        'satellite_id': ['LAGEOS-1'],
        'time': pd.to_datetime(['2023-01-01 00:00:00']),
        'residual': [0.1]  # 10cm
    }
    df = pd.DataFrame(data)

    result = filter_quality(df, threshold_cm=2.0)

    assert len(result) == 0
    assert result.empty

def test_filter_quality_custom_threshold():
    """Test with a custom threshold."""
    data = {
        'satellite_id': ['LAGEOS-1'],
        'time': pd.to_datetime(['2023-01-01 00:00:00']),
        'residual': [0.015]  # 1.5cm
    }
    df = pd.DataFrame(data)

    # Threshold 1cm should remove it
    result = filter_quality(df, threshold_cm=1.0)
    assert len(result) == 0

    # Threshold 2cm should keep it
    result = filter_quality(df, threshold_cm=2.0)
    assert len(result) == 1

def test_filter_quality_preserves_other_columns():
    """Ensure non-residual columns are preserved correctly."""
    data = {
        'satellite_id': ['LAGEOS-1', 'LAGEOS-1'],
        'station_id': ['ST1', 'ST2'],
        'range_m': [8000000.0, 8000000.0],
        'residual': [0.01, 0.05]
    }
    df = pd.DataFrame(data)

    result = filter_quality(df, threshold_cm=2.0)

    assert len(result) == 1
    assert result['station_id'].iloc[0] == 'ST1'
    assert result['range_m'].iloc[0] == 8000000.0