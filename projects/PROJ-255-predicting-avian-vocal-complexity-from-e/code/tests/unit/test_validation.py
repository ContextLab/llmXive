import pytest
import csv
import tempfile
from pathlib import Path
from src.analysis.validation import validate_osm_proxies, load_csv, save_csv

def test_validate_osm_proxies_interpolated():
    """Test that interpolated records are marked as INTERPOLATED."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        noise_mapped_path = tmpdir / "noise_mapped.csv"
        
        # Create noise_mapped.csv with an interpolated record
        records = [
            {'recording_id': 'rec1', 'source': 'interpolated', 'noise_level_db': '50.0'},
            {'recording_id': 'rec2', 'source': 'primary', 'noise_level_db': '55.0'}
        ]
        with open(noise_mapped_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        
        # Create empty reference data
        reference_data = []
        
        # Run validation
        logs = validate_osm_proxies(noise_mapped_path, reference_data)
        
        # Check results
        assert len(logs) == 2
        assert logs[0]['status'] == 'INTERPOLATED'
        assert logs[0]['recording_id'] == 'rec1'
        assert logs[0]['deviation'] is None

def test_validate_osm_proxies_pass():
    """Test that records with deviation <= 2 are marked as PASS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        noise_mapped_path = tmpdir / "noise_mapped.csv"
        ref_path = tmpdir / "reference.csv"
        
        # Create noise_mapped.csv
        noise_records = [
            {'recording_id': 'rec1', 'source': 'primary', 'noise_level_db': '50.0'}
        ]
        with open(noise_mapped_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=noise_records[0].keys())
            writer.writeheader()
            writer.writerows(noise_records)
        
        # Create reference data with close value
        ref_records = [
            {'recording_id': 'rec1', 'noise_level_db': '51.0'} # Deviation = 1.0
        ]
        with open(ref_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=ref_records[0].keys())
            writer.writeheader()
            writer.writerows(ref_records)
        
        reference_data = load_csv(ref_path)
        logs = validate_osm_proxies(noise_mapped_path, reference_data)
        
        assert len(logs) == 1
        assert logs[0]['status'] == 'PASS'
        assert logs[0]['deviation'] == 1.0

def test_validate_osm_proxies_warn():
    """Test that records with deviation > 2 are marked as WARN."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        noise_mapped_path = tmpdir / "noise_mapped.csv"
        ref_path = tmpdir / "reference.csv"
        
        # Create noise_mapped.csv
        noise_records = [
            {'recording_id': 'rec1', 'source': 'primary', 'noise_level_db': '50.0'}
        ]
        with open(noise_mapped_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=noise_records[0].keys())
            writer.writeheader()
            writer.writerows(noise_records)
        
        # Create reference data with far value
        ref_records = [
            {'recording_id': 'rec1', 'noise_level_db': '55.0'} # Deviation = 5.0
        ]
        with open(ref_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=ref_records[0].keys())
            writer.writeheader()
            writer.writerows(ref_records)
        
        reference_data = load_csv(ref_path)
        logs = validate_osm_proxies(noise_mapped_path, reference_data)
        
        assert len(logs) == 1
        assert logs[0]['status'] == 'WARN'
        assert logs[0]['deviation'] == 5.0

def test_validate_osm_proxies_no_reference():
    """Test that records without reference are marked as WARN."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        noise_mapped_path = tmpdir / "noise_mapped.csv"
        
        # Create noise_mapped.csv
        noise_records = [
            {'recording_id': 'rec1', 'source': 'primary', 'noise_level_db': '50.0'}
        ]
        with open(noise_mapped_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=noise_records[0].keys())
            writer.writeheader()
            writer.writerows(noise_records)
        
        # Empty reference
        reference_data = []
        logs = validate_osm_proxies(noise_mapped_path, reference_data)
        
        assert len(logs) == 1
        assert logs[0]['status'] == 'WARN'
        assert logs[0]['deviation'] is None
