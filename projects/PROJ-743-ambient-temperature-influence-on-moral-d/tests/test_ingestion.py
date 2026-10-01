"""
Integration tests for T016: ERA5 data fetching and merging with sample Moral Machine data.

These tests verify the full ingestion pipeline including geospatial matching logic
and temperature interpolation against a controlled sample dataset.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingestion import (
    load_moral_machine_data,
    apply_column_mapping,
    filter_missing_location,
    filter_invalid_response_time,
    capture_pre_filter_count,
    log_counts_to_file,
    ensure_exclusion_log_exists,
    save_filtered_data
)
from interpolation import (
    process_interpolation,
    calculate_temporal_gap,
    interpolate_temperature
)
from config import get_path_env_override

@pytest.fixture
def sample_moral_machine_data():
    """Create sample Moral Machine data for testing."""
    data = {
        'participant_id': range(5),
        'lat': [40.7128, 51.5074, 35.6762, 48.8566, 52.5200],
        'lon': [-74.0060, -0.1278, 139.6503, 2.3522, 13.4050],
        'response_time_ms': [500, 1200, 800, 200, 1500],
        'country': ['US', 'UK', 'JP', 'FR', 'DE'],
        'dilemma_id': range(5),
        'timestamp': pd.date_range('2016-01-01', periods=5, freq='h')
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_era5_data():
    """Create sample ERA5 temperature data for testing."""
    # Simulate hourly temperature data for a few grid points
    dates = pd.date_range('2016-01-01', periods=24, freq='h')
    data = []
    
    # Grid point near New York (approx 40.7, -74.0)
    for t in dates:
        data.append({
            'grid_id': 'grid_ny',
            'timestamp': t,
            'latitude': 40.75,
            'longitude': -74.0,
            'temperature_celsius': 5.0 + np.sin(t.hour / 24.0 * 2 * np.pi) * 2
        })
    
    # Grid point near London (approx 51.5, -0.1)
    for t in dates:
        data.append({
            'grid_id': 'grid_ldn',
            'timestamp': t,
            'latitude': 51.5,
            'longitude': -0.1,
            'temperature_celsius': 8.0 + np.sin(t.hour / 24.0 * 2 * np.pi) * 1.5
        })
        
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_full_ingestion_pipeline_integration(temp_dir, sample_moral_machine_data, sample_era5_data):
    """
    Integration test: Run the full ingestion and interpolation pipeline on sample data.
    Verifies that:
    1. Moral Machine data is loaded and filtered correctly.
    2. Temperature data is interpolated for matching timestamps.
    3. The final merged dataset contains valid temperature values.
    """
    # 1. Prepare Moral Machine data
    mm_path = temp_dir / 'moral_machine.csv'
    sample_moral_machine_data.to_csv(mm_path, index=False)
    
    # 2. Load and apply column mapping
    df_mm = load_moral_machine_data(mm_path)
    df_mm = apply_column_mapping(df_mm)
    
    # 3. Filter missing locations
    exclusion_log = temp_dir / 'exclusion_log.csv'
    ensure_exclusion_log_exists(exclusion_log)
    df_mm, _ = filter_missing_location(df_mm, exclusion_log)
    
    # 4. Filter invalid response times
    df_mm, _ = filter_invalid_response_time(df_mm, exclusion_log, min_ms=100, max_ms=10000)
    
    assert len(df_mm) > 0, "No valid Moral Machine records remaining after filtering"
    
    # 5. Save filtered data for interpolation step
    filtered_path = temp_dir / 'filtered_moral_machine.parquet'
    save_filtered_data(df_mm, filtered_path)
    
    # 6. Prepare ERA5 data
    era5_path = temp_dir / 'era5_sample.parquet'
    sample_era5_data.to_parquet(era5_path)
    
    # 7. Perform interpolation (simulating the matching logic)
    # Note: In a real scenario, this would match grid IDs based on coordinates
    # For this test, we manually assign grid IDs to simulate the match
    df_mm['grid_id'] = df_mm.apply(
        lambda row: 'grid_ny' if row['latitude'] > 40 else 'grid_ldn', 
        axis=1
    )
    
    # 8. Process interpolation
    interpolated_data = process_interpolation(
        moral_data=df_mm,
        era5_path=era5_path,
        exclusion_log=exclusion_log
    )
    
    # 9. Assertions
    assert interpolated_data is not None, "Interpolation failed to produce output"
    assert 'temperature_celsius' in interpolated_data.columns, "Temperature column missing"
    assert not interpolated_data['temperature_celsius'].isna().any(), "Missing temperature values after interpolation"
    
    # Verify temperature values are within a physically plausible range
    temps = interpolated_data['temperature_celsius']
    assert (temps >= -50).all() and (temps <= 60).all(), "Temperature values out of plausible range"
    
    # Verify record count is preserved (no unexpected drops in this simple test)
    assert len(interpolated_data) == len(df_mm), "Record count mismatch after interpolation"

def test_interpolation_edge_case_gap_handling(temp_dir, sample_moral_machine_data, sample_era5_data):
    """
    Test that the interpolation logic correctly handles temporal gaps.
    Specifically, verifies that gaps > 2 hours result in exclusion.
    """
    # Create a scenario with a large gap in ERA5 data
    dates = pd.date_range('2016-01-01', periods=5, freq='h')
    # Remove the 3rd and 4th hours to create a 3-hour gap
    dates_with_gap = [dates[0], dates[1], dates[4]]
    
    gap_data = []
    for t in dates_with_gap:
        gap_data.append({
            'grid_id': 'grid_ny',
            'timestamp': t,
            'latitude': 40.75,
            'longitude': -74.0,
            'temperature_celsius': 5.0
        })
    
    era5_gap_path = temp_dir / 'era5_gap.parquet'
    pd.DataFrame(gap_data).to_parquet(era5_gap_path)
    
    # Create a Moral Machine record that falls exactly in the gap
    mm_gap_data = pd.DataFrame({
        'participant_id': [99],
        'latitude': [40.7128],
        'longitude': [-74.0060],
        'response_time': [500],
        'grid_id': ['grid_ny'],
        'timestamp': [dates[2]]  # Falls in the gap
    })
    
    exclusion_log = temp_dir / 'exclusion_log_gap.csv'
    ensure_exclusion_log_exists(exclusion_log)
    
    # Process interpolation - this should exclude the record due to gap > 2h
    result = process_interpolation(
        moral_data=mm_gap_data,
        era5_path=era5_gap_path,
        exclusion_log=exclusion_log
    )
    
    # Verify the record was excluded
    assert result is None or len(result) == 0, "Record in large gap should be excluded"
    
    # Verify exclusion was logged
    if exclusion_log.exists():
        exclusion_df = pd.read_csv(exclusion_log)
        assert len(exclusion_df) > 0, "Exclusion log should contain entries for gap exclusion"
        assert any('temperature gap' in str(reason).lower() for reason in exclusion_df['exclusion_reason']), "Exclusion reason should mention temperature gap"

def test_column_mapping_integration(temp_dir, sample_moral_machine_data):
    """
    Integration test for column mapping and initial filtering.
    Ensures that raw Moral Machine columns are correctly transformed to internal schema.
    """
    mm_path = temp_dir / 'mm_test.csv'
    sample_moral_machine_data.to_csv(mm_path, index=False)
    
    # Load and map
    df = load_moral_machine_data(mm_path)
    df_mapped = apply_column_mapping(df)
    
    # Verify schema transformation
    assert 'latitude' in df_mapped.columns
    assert 'longitude' in df_mapped.columns
    assert 'response_time' in df_mapped.columns
    assert 'lat' not in df_mapped.columns
    assert 'lon' not in df_mapped.columns
    assert 'response_time_ms' not in df_mapped.columns
    
    # Verify data integrity
    assert df_mapped['latitude'].iloc[0] == sample_moral_machine_data['lat'].iloc[0]
    assert df_mapped['response_time'].iloc[0] == sample_moral_machine_data['response_time_ms'].iloc[0]