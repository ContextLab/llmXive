"""
Integration tests for User Story 1: Data Ingestion and Temperature Matching.
Specifically tests ERA5 data fetching (mocked for stability/speed in CI)
and merging with a sample of Moral Machine data.
"""
import os
import sys
import tempfile
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import DISTANCE_THRESHOLD_KM
from code.ingestion import (
    ensure_exclusion_log_exists,
    log_excluded_records,
    haversine_distance,
    match_geospatial_records,
    interpolate_temporal_gaps,
    main as ingestion_main
)

# Constants for test data
SAMPLE_MORAL_MACHINE_DATA = {
    "participant_id": ["P1", "P2", "P3", "P4", "P5"],
    "latitude": [51.5074, 40.7128, -33.8688, 35.6762, 999.0],  # London, NYC, Sydney, Tokyo, Invalid
    "longitude": [-0.1278, -74.0060, 151.2093, 139.6503, 0.0],
    "timestamp": pd.to_datetime([
        "2016-01-01 12:00:00",
        "2016-01-01 13:00:00",
        "2016-01-01 14:00:00",
        "2016-01-01 15:00:00",
        "2016-01-01 16:00:00"
    ]),
    "response_time": [2500, 1800, 3200, 2100, 500],  # ms
    "country": ["GB", "US", "AU", "JP", "XX"],
    "dilemma_id": ["D1", "D2", "D3", "D4", "D5"]
}

SAMPLE_ERA5_DATA = {
    "grid_id": ["GRID_LON", "GRID_NYC", "GRID_SYD", "GRID_TOK"],
    "latitude": [51.50, 40.71, -33.87, 35.68],
    "longitude": [-0.13, -74.01, 151.21, 139.65],
    "timestamp": pd.to_datetime([
        "2016-01-01 12:00:00",
        "2016-01-01 13:00:00",
        "2016-01-01 14:00:00",
        "2016-01-01 15:00:00"
    ]),
    "temperature_celsius": [8.5, 4.2, 22.1, 12.8]
}

@pytest.fixture
def temp_moral_machine_file():
    """Creates a temporary CSV file with sample Moral Machine data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame(SAMPLE_MORAL_MACHINE_DATA)
        # Ensure timestamp is string for CSV write/read consistency if needed,
        # but ingestion expects datetime or convertible string.
        df.to_csv(f, index=False)
        return f.name

@pytest.fixture
def temp_era5_file():
    """Creates a temporary Parquet file with sample ERA5 data."""
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        df = pd.DataFrame(SAMPLE_ERA5_DATA)
        df.to_parquet(f.name)
        return f.name

@pytest.fixture
def temp_output_dir():
    """Creates a temporary directory for output logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_haversine_distance():
    """Test the haversine distance calculation."""
    # London to NYC approx 5570 km
    dist = haversine_distance(51.5074, -0.1278, 40.7128, -74.0060)
    assert 5500 < dist < 5600

    # Same point
    dist = haversine_distance(51.5074, -0.1278, 51.5074, -0.1278)
    assert dist < 1.0

def test_match_geospatial_records(temp_moral_machine_file, temp_era5_file):
    """Test matching Moral Machine records to nearest ERA5 grid points."""
    mm_df = pd.read_csv(temp_moral_machine_file, parse_dates=['timestamp'])
    era5_df = pd.read_parquet(temp_era5_file)

    # Run matching
    matched_df = match_geospatial_records(mm_df, era5_df, DISTANCE_THRESHOLD_KM)

    # Check results
    # P1 (London) -> GRID_LON, dist ~ 0.8km
    # P2 (NYC) -> GRID_NYC, dist ~ 0.8km
    # P3 (Sydney) -> GRID_SYD, dist ~ 0.8km
    # P4 (Tokyo) -> GRID_TOK, dist ~ 0.8km
    # P5 (Invalid Lat) -> Should be excluded or have NaN distance if not filtered before
    
    # Verify specific matches
    london_row = matched_df[matched_df['participant_id'] == 'P1']
    assert not london_row.empty
    assert london_row.iloc[0]['matched_grid_id'] == 'GRID_LON'
    assert london_row.iloc[0]['match_quality'] == 'high' # Within threshold

    # Verify P5 (Invalid Lat 999)
    # Depending on implementation, it might be filtered out or have a huge distance.
    # If it remains, distance should be > threshold or quality 'low'.
    invalid_row = matched_df[matched_df['participant_id'] == 'P5']
    if not invalid_row.empty:
        # Should be flagged as low quality or excluded
        assert invalid_row.iloc[0]['match_quality'] in ['low', 'failed']

def test_interpolate_temporal_gaps(temp_moral_machine_file, temp_era5_file, temp_output_dir):
    """Test temporal interpolation logic."""
    mm_df = pd.read_csv(temp_moral_machine_file, parse_dates=['timestamp'])
    era5_df = pd.read_parquet(temp_era5_file)
    
    # Simulate a gap scenario: ERA5 has 12:00 and 14:00, MM is at 13:00
    # This would require interpolation.
    # For this test, we use the existing data which is aligned hour-by-hour.
    # We will test the function's ability to handle the merge without error.
    
    # First, match geospatially
    matched_df = match_geospatial_records(mm_df, era5_df, DISTANCE_THRESHOLD_KM)
    
    # Then interpolate
    # Note: The actual interpolation logic depends on the specific implementation in code/ingestion.py
    # This test ensures the pipeline runs without crashing on valid data.
    try:
        interpolated_df = interpolate_temporal_gaps(matched_df, era5_df)
        assert interpolated_df is not None
        assert 'temperature_celsius' in interpolated_df.columns
    except Exception as e:
        # If the implementation requires specific gap logic not met by sample data,
        # we ensure the error is not a silent failure.
        pytest.fail(f"Interpolation failed unexpectedly: {e}")

def test_ingestion_main_integration(temp_moral_machine_file, temp_era5_file, temp_output_dir):
    """
    End-to-end integration test for the ingestion script.
    Simulates the run of code/ingestion.py with sample data.
    """
    output_path = os.path.join(temp_output_dir, "merged_dataset.parquet")
    exclusion_log_path = os.path.join(temp_output_dir, "exclusion_log.csv")
    counts_log_path = os.path.join(temp_output_dir, "counts.json")

    # Mock the file paths to point to our temp files
    # We pass them as arguments to the main function if it accepts them,
    # or we patch the internal path resolution.
    # Assuming main() accepts --input, --temp, --output arguments as per run-book.
    
    with patch('sys.argv', [
        'test',
        '--input', temp_moral_machine_file,
        '--temp', temp_era5_file,
        '--output', output_path,
        '--exclusion-log', exclusion_log_path,
        '--counts-log', counts_log_path
    ]):
        try:
            ingestion_main()
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"ingestion_main exited with code {e.code}")

    # Verify outputs exist
    assert os.path.exists(output_path), "Merged dataset was not created."
    assert os.path.exists(exclusion_log_path), "Exclusion log was not created."
    
    # Verify content
    merged_df = pd.read_parquet(output_path)
    assert len(merged_df) > 0, "Merged dataset is empty."
    assert 'temperature_celsius' in merged_df.columns, "Temperature column missing."
    assert 'match_quality' in merged_df.columns, "Match quality column missing."

    # Verify counts log
    assert os.path.exists(counts_log_path), "Counts log not created."
    with open(counts_log_path, 'r') as f:
        counts = json.load(f)
    assert 'count_filtered_for_analysis' in counts or 'count_matched_pre_exclusion' in counts, \
        "Expected count keys missing in log."

def test_filtering_logic(temp_moral_machine_file, temp_era5_file, temp_output_dir):
    """
    Test that invalid response times and missing locations are filtered.
    """
    # Modify sample data to include invalid response times
    mm_data = SAMPLE_MORAL_MACHINE_DATA.copy()
    mm_data['response_time'] = [2500, 50, 3200, 15000, 500] # 50ms and 15000ms are invalid
    mm_data['latitude'] = [51.5074, 40.7128, None, 35.6762, 999.0] # One missing, one invalid

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        pd.DataFrame(mm_data).to_csv(f, index=False)
        temp_mm = f.name

    output_path = os.path.join(temp_output_dir, "merged_filtered.parquet")
    exclusion_log_path = os.path.join(temp_output_dir, "exclusion_log_filtered.csv")

    with patch('sys.argv', [
        'test',
        '--input', temp_mm,
        '--temp', temp_era5_file,
        '--output', output_path,
        '--exclusion-log', exclusion_log_path
    ]):
        try:
            ingestion_main()
        except SystemExit as e:
            if e.code != 0:
                pytest.fail(f"ingestion_main exited with code {e.code}")

    # Check exclusion log
    exclusion_df = pd.read_csv(exclusion_log_path)
    reasons = exclusion_df['reason'].tolist()
    
    # Should have exclusions for missing location and invalid response time
    assert 'missing location' in reasons or 'invalid response time' in reasons, \
        f"Expected exclusions not found. Reasons: {reasons}"

    # Check merged output count
    merged_df = pd.read_parquet(output_path)
    # Original 5 rows.
    # P3: Missing lat -> Excluded
    # P5: Invalid lat (999) -> Likely excluded or low quality
    # P2: 50ms -> Excluded
    # P4: 15000ms -> Excluded
    # P1: Valid -> Included
    # So we expect very few or 1 row.
    assert len(merged_df) <= 1, "Too many rows survived filtering."

if __name__ == '__main__':
    pytest.main([__file__, '-v'])