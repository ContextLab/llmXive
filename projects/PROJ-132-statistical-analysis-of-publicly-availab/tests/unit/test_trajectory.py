"""
Unit tests for src/models/trajectory.py

Tests for:
- compute_weekly_centroids
- filter_centroids_by_data_quality
- run_trajectory_pipeline
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Import the module under test
from src.models.trajectory import (
    compute_weekly_centroids,
    filter_centroids_by_data_quality,
    run_trajectory_pipeline
)

@pytest.fixture
def sample_weekly_data():
    """Create sample weekly grid data for testing."""
    data = {
        'species': ['SpeciesA', 'SpeciesA', 'SpeciesA', 'SpeciesB', 'SpeciesB'],
        'year': [2020, 2020, 2020, 2020, 2020],
        'week': [10, 10, 11, 10, 10],
        'grid_cell': ['cell1', 'cell2', 'cell1', 'cell1', 'cell1'],
        'count': [10, 20, 5, 100, 0],  # Last one has 0 count
        'lat': [40.0, 41.0, 40.5, 35.0, 36.0],
        'lon': [-75.0, -74.0, -74.5, -80.0, -79.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)

def test_compute_weekly_centroids_basic(sample_weekly_data):
    """Test basic centroid computation."""
    result = compute_weekly_centroids(sample_weekly_data)
    
    # Check columns
    expected_cols = ['species', 'year', 'week', 'centroid_lat', 'centroid_lon', 'total_count']
    assert list(result.columns) == expected_cols
    
    # Check row count (SpeciesA has 2 weeks, SpeciesB has 1 week with count > 0)
    assert len(result) == 3
    
    # Verify SpeciesA week 10 centroid calculation manually:
    # Counts: 10 (lat 40), 20 (lat 41) -> Total 30
    # Weighted Lat: (10*40 + 20*41) / 30 = (400 + 820) / 30 = 1220 / 30 = 40.666...
    species_a_week_10 = result[(result['species'] == 'SpeciesA') & (result['week'] == 10)]
    assert len(species_a_week_10) == 1
    assert abs(species_a_week_10['centroid_lat'].values[0] - 40.666666666666664) < 1e-5
    assert species_a_week_10['total_count'].values[0] == 30
    
    # Verify SpeciesB week 10 (only one record with count > 0)
    species_b_week_10 = result[(result['species'] == 'SpeciesB') & (result['week'] == 10)]
    assert len(species_b_week_10) == 1
    assert species_b_week_10['centroid_lat'].values[0] == 35.0
    assert species_b_week_10['total_count'].values[0] == 100

def test_compute_weekly_centroids_empty_input():
    """Test centroid computation with empty DataFrame."""
    empty_df = pd.DataFrame(columns=['species', 'year', 'week', 'count', 'lat', 'lon'])
    result = compute_weekly_centroids(empty_df)
    assert len(result) == 0
    assert list(result.columns) == ['species', 'year', 'week', 'centroid_lat', 'centroid_lon', 'total_count']

def test_compute_weekly_centroids_missing_columns(sample_weekly_data):
    """Test centroid computation with missing required columns."""
    incomplete_df = sample_weekly_data.drop(columns=['count'])
    with pytest.raises(ValueError, match="Missing required columns"):
        compute_weekly_centroids(incomplete_df)

def test_filter_centroids_by_data_quality(sample_weekly_data):
    """Test filtering of centroids based on data quality."""
    # First compute centroids
    centroids = compute_weekly_centroids(sample_weekly_data)
    
    # Filter with threshold 5
    filtered = filter_centroids_by_data_quality(centroids, quality_threshold=5)
    
    # Check that rows with total_count < 5 are removed
    assert all(filtered['total_count'] >= 5)
    
    # Check that rows with total_count >= 5 are kept
    # In our sample, SpeciesA week 10 has 30, SpeciesA week 11 has 5, SpeciesB week 10 has 100
    # All should be kept with threshold 5
    assert len(filtered) == 3
    
    # Filter with threshold 10
    filtered_high = filter_centroids_by_data_quality(centroids, quality_threshold=10)
    # SpeciesA week 11 (count 5) should be removed
    assert len(filtered_high) == 2
    assert not ((filtered_high['species'] == 'SpeciesA') & (filtered_high['week'] == 11)).any()

def test_run_trajectory_pipeline(sample_weekly_data, temp_data_dir):
    """Test the full pipeline integration."""
    input_path = temp_data_dir / "weekly_grid_data.parquet"
    output_path = temp_data_dir / "trajectory_centroids.json"
    
    # Save sample data
    sample_weekly_data.to_parquet(input_path)
    
    # Run pipeline
    result = run_trajectory_pipeline(input_path, output_path, quality_threshold=5)
    
    # Check output file exists
    assert output_path.exists()
    
    # Check result DataFrame
    assert len(result) == 3
    assert 'centroid_lat' in result.columns
    
    # Check output JSON content
    import json
    with open(output_path, 'r') as f:
        data = json.load(f)
    assert len(data) == 3
    assert 'centroid_lat' in data[0]

def test_run_trajectory_pipeline_csv_input(sample_weekly_data, temp_data_dir):
    """Test pipeline with CSV input."""
    input_path = temp_data_dir / "weekly_grid_data.csv"
    output_path = temp_data_dir / "trajectory_centroids.json"
    
    # Save sample data as CSV
    sample_weekly_data.to_csv(input_path, index=False)
    
    # Run pipeline
    result = run_trajectory_pipeline(input_path, output_path, quality_threshold=5)
    
    assert output_path.exists()
    assert len(result) == 3

def test_run_trajectory_pipeline_missing_input(temp_data_dir):
    """Test pipeline with missing input file."""
    input_path = temp_data_dir / "nonexistent.parquet"
    output_path = temp_data_dir / "trajectory_centroids.json"
    
    with pytest.raises(FileNotFoundError):
        run_trajectory_pipeline(input_path, output_path)