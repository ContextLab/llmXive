import pytest
import os
import logging
import tempfile
import csv
from pathlib import Path

# Import the function under test
from preprocess import filter_missing_environmental_data, save_flagged_env_data

@pytest.fixture
def sample_records():
    """Fixture providing a list of sample records with varying environmental data completeness."""
    return [
        {"id": "rec_001", "smiles": "CCO", "temperature": 25.0, "ph": 7.0, "uv_intensity": 100.0},
        {"id": "rec_002", "smiles": "CC(=O)O", "temperature": 30.0, "ph": None, "uv_intensity": 100.0}, # Missing pH
        {"id": "rec_003", "smiles": "C1=CC=CC=C1", "temperature": None, "ph": 5.0, "uv_intensity": 50.0}, # Missing Temp
        {"id": "rec_004", "smiles": "CCO", "temperature": 20.0, "ph": 6.0, "uv_intensity": None}, # Missing UV
        {"id": "rec_005", "smiles": "CCCC", "temperature": 40.0, "ph": 8.0, "uv_intensity": 200.0}, # Complete
        {"id": "rec_006", "smiles": "CCO", "temperature": None, "ph": None, "uv_intensity": None}, # All missing
    ]

@pytest.fixture
def logger():
    return logging.getLogger("test_preprocess")

def test_filter_missing_environmental_data_excludes_missing_temp(sample_records, logger):
    """Test that records with missing temperature are excluded and flagged."""
    valid, flagged = filter_missing_environmental_data(sample_records, logger)
    
    # rec_003 has missing temp, rec_006 has all missing
    assert "rec_003" in flagged
    assert "rec_006" in flagged
    
    # Check that valid records do not contain the flagged ones
    valid_ids = [r['id'] for r in valid]
    assert "rec_003" not in valid_ids
    assert "rec_006" not in valid_ids

def test_filter_missing_environmental_data_excludes_missing_ph(sample_records, logger):
    """Test that records with missing pH are excluded and flagged."""
    valid, flagged = filter_missing_environmental_data(sample_records, logger)
    
    assert "rec_002" in flagged
    valid_ids = [r['id'] for r in valid]
    assert "rec_002" not in valid_ids

def test_filter_missing_environmental_data_excludes_missing_uv(sample_records, logger):
    """Test that records with missing UV are excluded and flagged."""
    valid, flagged = filter_missing_environmental_data(sample_records, logger)
    
    assert "rec_004" in flagged
    valid_ids = [r['id'] for r in valid]
    assert "rec_004" not in valid_ids

def test_filter_missing_environmental_data_keeps_complete(sample_records, logger):
    """Test that records with complete environmental data are kept."""
    valid, flagged = filter_missing_environmental_data(sample_records, logger)
    
    assert "rec_001" not in flagged
    assert "rec_005" not in flagged
    
    valid_ids = [r['id'] for r in valid]
    assert "rec_001" in valid_ids
    assert "rec_005" in valid_ids

def test_save_flagged_env_data_creates_csv(tmp_path, logger):
    """Test that save_flagged_env_data creates a valid CSV file."""
    flagged_ids = ["rec_002", "rec_003", "rec_006"]
    output_path = tmp_path / "flagged_env_data.csv"
    
    save_flagged_env_data(flagged_ids, str(output_path), logger)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]['record_id'] == "rec_002"
    assert rows[0]['reason'] == "Missing environmental data (temp/pH/UV)"

def test_filter_with_empty_list(logger):
    """Test behavior with an empty list of records."""
    valid, flagged = filter_missing_environmental_data([], logger)
    assert len(valid) == 0
    assert len(flagged) == 0
