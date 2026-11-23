"""
Unit tests for observer effort calculation in preprocess.py
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

from src.data.preprocess import calculate_observer_effort, aggregate_to_weekly_grid


@pytest.fixture
def sample_ebird_data():
    """Create sample eBird data for testing observer effort calculation."""
    data = {
        'species': ['AMCR', 'AMCR', 'AMCR', 'ARCR', 'ARCR', 'AMCR'],
        'lat': [40.5, 40.5, 40.6, 41.0, 41.0, 40.5],
        'lon': [-74.0, -74.0, -74.1, -73.5, -73.5, -74.0],
        'date': [
            '2023-03-15', '2023-03-15', '2023-03-22',
            '2023-03-15', '2023-03-22', '2023-03-15'
        ],
        'count': [5, 3, 7, 2, 4, 6],
        'checklist_id': ['chk1', 'chk2', 'chk3', 'chk4', 'chk5', 'chk1']
    }
    return pd.DataFrame(data)


def test_calculate_observer_effort_basic(sample_ebird_data):
    """Test that observer effort columns are added correctly."""
    # First aggregate to weekly grid
    aggregated = aggregate_to_weekly_grid(sample_ebird_data)

    # Calculate observer effort
    result = calculate_observer_effort(aggregated)

    # Check that effort columns exist
    assert 'observer_effort_checklists' in result.columns
    assert 'observer_effort_hours' in result.columns
    assert 'observer_effort_distance_km' in result.columns
    assert 'log_observer_effort_hours' in result.columns
    assert 'log_observer_effort_distance_km' in result.columns

    # Check that checklist count is preserved
    assert result['observer_effort_checklists'].min() >= 1


def test_calculate_observer_effort_values(sample_ebird_data):
    """Test that observer effort values are calculated correctly."""
    aggregated = aggregate_to_weekly_grid(sample_ebird_data)
    result = calculate_observer_effort(aggregated)

    # Typical duration is 1.5 hours
    typical_duration = 1.5

    # Check hours calculation
    expected_hours = result['observer_effort_checklists'] * typical_duration
    pd.testing.assert_series_equal(
        result['observer_effort_hours'],
        expected_hours,
        check_names=False
    )

    # Typical distance is 2 km
    typical_distance = 2.0
    expected_distance = result['observer_effort_checklists'] * typical_distance
    pd.testing.assert_series_equal(
        result['observer_effort_distance_km'],
        expected_distance,
        check_names=False
    )

    # Check log transformation
    expected_log_hours = np.log1p(result['observer_effort_hours'])
    pd.testing.assert_series_equal(
        result['log_observer_effort_hours'],
        expected_log_hours,
        check_names=False
    )


def test_calculate_observer_effort_empty_input():
    """Test observer effort calculation with empty DataFrame."""
    empty_df = pd.DataFrame(columns=[
        'species', 'grid_cell', 'week', 'year', 'checklist_count'
    ])

    result = calculate_observer_effort(empty_df)

    assert 'observer_effort_checklists' in result.columns
    assert len(result) == 0


def test_calculate_observer_effort_single_checklist():
    """Test with single checklist per grid cell."""
    data = {
        'species': ['AMCR'],
        'grid_cell': ['40.5_-74.0'],
        'week': [11],
        'year': [2023],
        'checklist_count': [1]
    }
    df = pd.DataFrame(data)

    result = calculate_observer_effort(df)

    assert result['observer_effort_checklists'].iloc[0] == 1
    assert result['observer_effort_hours'].iloc[0] == 1.5
    assert result['observer_effort_distance_km'].iloc[0] == 2.0


def test_calculate_observer_effort_multiple_checklists():
    """Test with multiple checklists per grid cell."""
    data = {
        'species': ['AMCR'],
        'grid_cell': ['40.5_-74.0'],
        'week': [11],
        'year': [2023],
        'checklist_count': [10]
    }
    df = pd.DataFrame(data)

    result = calculate_observer_effort(df)

    assert result['observer_effort_checklists'].iloc[0] == 10
    assert result['observer_effort_hours'].iloc[0] == 15.0
    assert result['observer_effort_distance_km'].iloc[0] == 20.0