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
    is_point_in_bbox,
    process_song_records,
    process_climate_snapshots,
    perform_spatial_join,
    detect_crs_from_metadata,
    save_processed_data,
    save_excluded_species
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

def test_is_point_in_bbox():
    bbox = {'min_lat': 40, 'max_lat': 50, 'min_lon': -100, 'max_lon': -90}
    assert is_point_in_bbox(45, -95, bbox)
    assert not is_point_in_bbox(30, -95, bbox)
    assert not is_point_in_bbox(45, -80, bbox)

def test_detect_crs_from_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['lat', 'lon'])
            writer.writeheader()
            writer.writerow({'lat': 45.0, 'lon': -93.0})
        
        crs = detect_crs_from_metadata(csv_path)
        assert crs == "EPSG:4326"

def test_process_song_records(tmp_path):
    # Create test input
    input_dir = tmp_path / "data" / "raw"
    input_dir.mkdir(parents=True)
    input_file = input_dir / "xeno_canto_metadata.csv"
    
    with open(input_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['species_id', 'lat', 'lon', 'song_metric_1', 'song_metric_2'])
        writer.writeheader()
        writer.writerow({'species_id': 'Q123', 'lat': 45.0, 'lon': -93.0, 'song_metric_1': 2.5, 'song_metric_2': 1.2})
    
    config = Config()
    records = process_song_records(input_file, config)
    
    assert len(records) == 1
    assert records[0]['species_id'] == 'Q123'
    assert records[0]['lat'] == 45.0

def test_process_climate_snapshots(tmp_path):
    input_dir = tmp_path / "data" / "raw"
    input_dir.mkdir(parents=True)
    input_file = input_dir / "worldclim_data.csv"
    
    with open(input_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['lat', 'lon', 'temperature', 'precipitation', 'elevation'])
        writer.writeheader()
        writer.writerow({'lat': 45.0, 'lon': -93.0, 'temperature': 15.0, 'precipitation': 800, 'elevation': 300})
    
    config = Config()
    records = process_climate_snapshots(input_file, config)
    
    assert len(records) == 1
    assert records[0]['temperature'] == 15.0

def test_perform_spatial_join(tmp_path):
    # Setup test data
    song_records = [{'species_id': 'Q1', 'lat': 45.0, 'lon': -93.0, 'song_metric_1': 2.5}]
    climate_records = [{'lat': 45.0, 'lon': -93.0, 'temperature': 15.0}]
    
    joined, excluded = perform_spatial_join(song_records, climate_records, radius_km=10)
    
    assert len(joined) == 1
    assert len(excluded) == 0
    assert joined[0]['species_id'] == 'Q1'
    assert joined[0]['temperature'] == 15.0

def test_save_processed_data(tmp_path):
    data = [{'species_id': 'Q1', 'lat': 45.0, 'lon': -93.0}]
    output_path = tmp_path / "output.csv"
    
    save_processed_data(data, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]['species_id'] == 'Q1'

def test_save_excluded_species(tmp_path):
    excluded = ['Q1', 'Q2']
    output_path = tmp_path / "excluded.json"
    
    save_excluded_species(excluded, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
        assert data['count'] == 2
        assert 'Q1' in data['excluded_ids']