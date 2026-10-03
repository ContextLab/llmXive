import pytest
import os
import sys
from pathlib import Path
import csv
import json
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import (
    haversine_distance,
    perform_spatial_join,
    calculate_match_rate,
    verify_no_duplicates
)
from utils import (
    load_schema,
    validate_song_record,
    validate_climate_snapshot,
    validate_analysis_dataset
)
from config import Config

def test_haversine_distance():
    # Distance between two known points
    lat1, lon1 = 45.0, -93.0
    lat2, lon2 = 45.0, -92.0
    dist = haversine_distance(lat1, lon1, lat2, lon2)
    assert dist > 0
    # Approx 80km for 1 degree longitude at 45 deg lat
    assert 70 < dist < 90

def test_schema_validation_song_record():
    """Test validation logic for song record schema."""
    schema = load_schema("contracts/song_record.schema.yaml")
    
    # Valid record
    valid_record = {
        "species_id": "Q123",
        "lat": 45.0,
        "lon": -93.0,
        "song_metric_1": 2.5,
        "song_metric_2": 1.2
    }
    result = validate_song_record(valid_record, schema)
    assert result is True

    # Missing required field
    invalid_record = {
        "species_id": "Q123",
        "lat": 45.0
    }
    result = validate_song_record(invalid_record, schema)
    assert result is False

    # Invalid coordinate type
    invalid_record = {
        "species_id": "Q123",
        "lat": "not_a_number",
        "lon": -93.0,
        "song_metric_1": 2.5,
        "song_metric_2": 1.2
    }
    result = validate_song_record(invalid_record, schema)
    assert result is False

def test_schema_validation_climate_snapshot():
    """Test validation logic for climate snapshot schema."""
    schema = load_schema("contracts/climate_snapshot.schema.yaml")
    
    # Valid record
    valid_record = {
        "lat": 45.0,
        "lon": -93.0,
        "temperature": 15.0,
        "precipitation": 800,
        "elevation": 300
    }
    result = validate_climate_snapshot(valid_record, schema)
    assert result is True

    # Missing required field
    invalid_record = {
        "lat": 45.0,
        "lon": -93.0,
        "temperature": 15.0
    }
    result = validate_climate_snapshot(invalid_record, schema)
    assert result is False

def test_schema_validation_analysis_dataset():
    """Test validation logic for merged analysis dataset schema."""
    schema = load_schema("contracts/analysis_dataset.schema.yaml")
    
    # Valid merged record
    valid_record = {
        "species_id": "Q123",
        "lat": 45.0,
        "lon": -93.0,
        "song_metric_1": 2.5,
        "song_metric_2": 1.2,
        "temperature": 15.0,
        "precipitation": 800,
        "elevation": 300
    }
    result = validate_analysis_dataset(valid_record, schema)
    assert result is True

    # Missing song metric
    invalid_record = {
        "species_id": "Q123",
        "lat": 45.0,
        "lon": -93.0,
        "song_metric_1": 2.5,
        "temperature": 15.0,
        "precipitation": 800,
        "elevation": 300
    }
    result = validate_analysis_dataset(invalid_record, schema)
    assert result is False

def test_perform_spatial_join():
    # Setup test data
    song_records = [
        {'species_id': 'Q1', 'lat': 45.0, 'lon': -93.0, 'song_metric_1': 2.5},
        {'species_id': 'Q2', 'lat': 45.1, 'lon': -93.1, 'song_metric_1': 3.0}
    ]
    climate_records = [
        {'lat': 45.0, 'lon': -93.0, 'temperature': 15.0},
        {'lat': 45.1, 'lon': -93.1, 'temperature': 14.5}
    ]

    joined, excluded = perform_spatial_join(song_records, climate_records, radius_km=10)

    assert len(joined) == 2
    assert len(excluded) == 0
    assert joined[0]['species_id'] == 'Q1'
    assert joined[0]['temperature'] == 15.0
    assert joined[1]['species_id'] == 'Q2'
    assert joined[1]['temperature'] == 14.5

def test_perform_spatial_join_no_match():
    # Setup test data with no matches
    song_records = [
        {'species_id': 'Q1', 'lat': 0.0, 'lon': 0.0, 'song_metric_1': 2.5}
    ]
    climate_records = [
        {'lat': 90.0, 'lon': 180.0, 'temperature': 15.0}
    ]

    joined, excluded = perform_spatial_join(song_records, climate_records, radius_km=10)

    assert len(joined) == 0
    assert len(excluded) == 1
    assert excluded[0]['species_id'] == 'Q1'

def test_calculate_match_rate():
    total = 100
    matched = 85
    rate = calculate_match_rate(matched, total)
    assert rate == 0.85
    assert 0.0 <= rate <= 1.0

def test_calculate_match_rate_zero_total():
    # Should handle division by zero gracefully (return 0.0 or raise)
    # Based on safe_divide utility usage
    rate = calculate_match_rate(0, 0)
    assert rate == 0.0

def test_verify_no_duplicates():
    # Valid unique records
    records = [
        {'id': 1, 'val': 'a'},
        {'id': 2, 'val': 'b'}
    ]
    assert verify_no_duplicates(records, key='id') is True

    # Duplicate records
    records = [
        {'id': 1, 'val': 'a'},
        {'id': 1, 'val': 'c'}
    ]
    assert verify_no_duplicates(records, key='id') is False

    # Empty list
    assert verify_no_duplicates([], key='id') is True