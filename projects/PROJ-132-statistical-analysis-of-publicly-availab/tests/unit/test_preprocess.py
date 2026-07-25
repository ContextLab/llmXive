"""
Unit tests for the preprocessing pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import os

from src.data.preprocess import (
    filter_migratory_species,
    assign_grid_cell,
    add_grid_cells,
    aggregate_to_weekly_grid,
    compute_phenology_metrics,
    mark_insufficient_data,
    calculate_observer_effort,
    apply_tail_preserving_sampling
)


@pytest.fixture
def sample_ebird_data():
    """Create sample eBird data for testing."""
    data = {
        'species': [
            'American Robin', 'American Robin', 'Blue Jay', 'Red-winged Blackbird',
            'House Sparrow', 'American Robin', 'Blue Jay'
        ],
        'lat': [40.1, 40.2, 40.15, 40.25, 40.1, 40.3, 40.18],
        'lon': [-74.1, -74.2, -74.15, -74.25, -74.1, -74.3, -74.18],
        'date': [
            '2023-03-01', '2023-03-08', '2023-03-05', '2023-03-10',
            '2023-03-01', '2023-03-15', '2023-03-12'
        ],
        'count': [5, 3, 2, 8, 10, 4, 3],
        'checklist_id': ['chk1', 'chk2', 'chk3', 'chk4', 'chk5', 'chk6', 'chk7']
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_phenology_data():
    """Create sample phenology data for testing."""
    data = {
        'species': ['American Robin', 'American Robin', 'Blue Jay'],
        'grid_lat': [40.0, 40.5, 40.0],
        'grid_lon': [-74.0, -74.0, -74.0],
        'first_arrival': [
            pd.Timestamp('2023-03-01'),
            pd.Timestamp('2023-03-15'),
            pd.Timestamp('2023-03-05')
        ],
        'median_arrival': [
            pd.Timestamp('2023-03-10'),
            pd.Timestamp('2023-03-20'),
            pd.Timestamp('2023-03-12')
        ],
        'stopover_duration': [4.0, 3.0, 5.0],
        'total_observations': [10, 5, 8],
        'total_count': [50, 25, 40],
        'sufficient_data': [True, True, True]
    }
    return pd.DataFrame(data)


def test_filter_migratory_species(sample_ebird_data):
    """Test that migratory species are correctly filtered."""
    filtered = filter_migratory_species(sample_ebird_data)

    # House Sparrow should be excluded (not in migratory list)
    assert 'House Sparrow' not in filtered['species'].values
    assert len(filtered) == 6  # 7 original - 1 non-migratory


def test_assign_grid_cell():
    """Test grid cell assignment."""
    # Test with 0.5 degree resolution
    lat, lon = assign_grid_cell(40.12, -74.18, grid_res=0.5)
    assert lat == 40.0
    assert lon == -74.0

    lat, lon = assign_grid_cell(40.62, -74.68, grid_res=0.5)
    assert lat == 40.5
    assert lon == -74.5


def test_add_grid_cells(sample_ebird_data):
    """Test that grid cells are correctly added."""
    df_with_grid = add_grid_cells(sample_ebird_data, grid_res=0.5)

    assert 'grid_lat' in df_with_grid.columns
    assert 'grid_lon' in df_with_grid.columns

    # Check that grid cells are rounded to 0.5 degrees
    for _, row in df_with_grid.iterrows():
        assert row['grid_lat'] % 0.5 == 0
        assert row['grid_lon'] % 0.5 == 0


def test_aggregate_to_weekly_grid(sample_ebird_data):
    """Test weekly aggregation."""
    df_with_grid = add_grid_cells(sample_ebird_data, grid_res=0.5)
    aggregated = aggregate_to_weekly_grid(df_with_grid)

    assert 'week_start' in aggregated.columns
    assert 'count' in aggregated.columns
    assert len(aggregated) > 0


def test_compute_phenology_metrics(sample_ebird_data):
    """Test phenology metric computation."""
    df_with_grid = add_grid_cells(sample_ebird_data, grid_res=0.5)
    weekly = aggregate_to_weekly_grid(df_with_grid)
    phenology = compute_phenology_metrics(weekly)

    assert 'first_arrival' in phenology.columns
    assert 'median_arrival' in phenology.columns
    assert 'stopover_duration' in phenology.columns
    assert 'total_observations' in phenology.columns
    assert len(phenology) > 0


def test_mark_insufficient_data(sample_phenology_data):
    """Test marking of insufficient data."""
    marked = mark_insufficient_data(sample_phenology_data, min_observations=6)

    assert 'sufficient_data' in marked.columns
    # First record has 10 observations, should be sufficient
    assert marked.iloc[0]['sufficient_data'] == True
    # Second record has 5 observations, should be insufficient with min=6
    assert marked.iloc[1]['sufficient_data'] == False
    # Third record has 8 observations, should be sufficient
    assert marked.iloc[2]['sufficient_data'] == True


def test_calculate_observer_effort(sample_ebird_data):
    """Test observer effort calculation."""
    df_with_grid = add_grid_cells(sample_ebird_data, grid_res=0.5)
    weekly = aggregate_to_weekly_grid(df_with_grid)
    effort_df = calculate_observer_effort(weekly)

    assert 'effort' in effort_df.columns
    assert len(effort_df) == len(weekly)


def test_tail_preserving_sampling(sample_phenology_data):
    """Test tail-preserving stratified sampling."""
    weighted = apply_tail_preserving_sampling(sample_phenology_data)

    assert 'weight' in weighted.columns
    assert 'arrival_decile' in weighted.columns

    # Check that weights are either 0.5 or 1.0
    assert all(weighted['weight'].isin([0.5, 1.0]))


def test_empty_dataframe_handling():
    """Test handling of empty DataFrames."""
    empty_df = pd.DataFrame(columns=['species', 'lat', 'lon', 'date', 'count', 'checklist_id'])

    filtered = filter_migratory_species(empty_df)
    assert len(filtered) == 0

    aggregated = aggregate_to_weekly_grid(empty_df)
    assert len(aggregated) == 0

    phenology = compute_phenology_metrics(aggregated)
    assert len(phenology) == 0


def test_missing_columns():
    """Test handling of missing columns."""
    incomplete_df = pd.DataFrame({'species': ['American Robin'], 'lat': [40.1]})

    with pytest.raises(KeyError):
        add_grid_cells(incomplete_df)

    with pytest.raises(KeyError):
        aggregate_to_weekly_grid(incomplete_df)
