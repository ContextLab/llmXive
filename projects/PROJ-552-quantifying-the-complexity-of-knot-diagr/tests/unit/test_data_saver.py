"""
Unit tests for data_saver.py module (T018).

Tests:
- save_raw_data: Verifies raw data is saved to JSON
- save_cleaned_data: Verifies cleaned data is saved to CSV
- save_raw_and_cleaned_data: Tests complete pipeline
"""

import json
import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from download.knot_atlas_loader import KnotRecord
from data.parser import ParsedKnotData
from data.data_saver import DataSaver, save_raw_and_cleaned_data


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_knot_record():
    """Create a sample KnotRecord for testing."""
    return KnotRecord(
        knot_id="3_1",
        crossing_number=3,
        braid_index=2,
        hyperbolic_volume=0.533349,
        is_alternating=True,
        dt_code="4 -2",
        braid_word="s1 s1"
    )

@pytest.fixture
def sample_parsed_record():
    """Create a sample ParsedKnotData for testing."""
    return ParsedKnotData(
        knot_id="3_1",
        crossing_number=3,
        braid_index=2,
        hyperbolic_volume=0.533349,
        is_alternating=True,
        dt_code="4 -2",
        braid_word="s1 s1"
    )

def test_save_raw_data_creates_json_file(temp_project_root, sample_knot_record):
    """Test that save_raw_data creates a valid JSON file."""
    saver = DataSaver(temp_project_root)
    records = [sample_knot_record, sample_knot_record]
    
    # Save raw data
    raw_path = saver.save_raw_data(records)
    
    # Verify file exists
    assert raw_path.exists()
    assert raw_path.name == "knot_atlas_raw.json"
    
    # Verify JSON is valid
    with open(raw_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['knot_id'] == "3_1"
    assert data[0]['crossing_number'] == 3

def test_save_raw_data_creates_directory(temp_project_root, sample_knot_record):
    """Test that save_raw_data creates the data/raw directory if needed."""
    saver = DataSaver(temp_project_root)
    records = [sample_knot_record]
    
    # Directory should not exist yet
    raw_dir = temp_project_root / "data" / "raw"
    assert not raw_dir.exists()
    
    # Save data
    saver.save_raw_data(records)
    
    # Directory should now exist
    assert raw_dir.exists()
    assert raw_dir.is_dir()

def test_save_cleaned_data_creates_csv_file(temp_project_root, sample_parsed_record):
    """Test that save_cleaned_data creates a valid CSV file."""
    saver = DataSaver(temp_project_root)
    records = [sample_parsed_record, sample_parsed_record]
    
    # Save cleaned data
    cleaned_path = saver.save_cleaned_data(records)
    
    # Verify file exists
    assert cleaned_path.exists()
    assert cleaned_path.name == "knots_cleaned.csv"
    
    # Verify CSV is valid
    with open(cleaned_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['knot_id'] == "3_1"
    assert rows[0]['crossing_number'] == "3"
    assert 'crossing_number' in reader.fieldnames
    assert 'braid_index' in reader.fieldnames
    assert 'hyperbolic_volume' in reader.fieldnames

def test_save_cleaned_data_creates_directory(temp_project_root, sample_parsed_record):
    """Test that save_cleaned_data creates the data/processed directory if needed."""
    saver = DataSaver(temp_project_root)
    records = [sample_parsed_record]
    
    # Directory should not exist yet
    processed_dir = temp_project_root / "data" / "processed"
    assert not processed_dir.exists()
    
    # Save data
    saver.save_cleaned_data(records)
    
    # Directory should now exist
    assert processed_dir.exists()
    assert processed_dir.is_dir()

def test_save_cleaned_data_with_flags(temp_project_root, sample_parsed_record):
    """Test that save_cleaned_data includes flags when provided."""
    saver = DataSaver(temp_project_root)
    records = [sample_parsed_record]
    
    # Create mock flags
    mock_flags = Mock()
    mock_flags.get_flags = Mock(return_value=Mock(to_json=Mock(return_value='{"test": "flag"}')))
    
    # Save with flags
    cleaned_path = saver.save_cleaned_data(records, mock_flags)
    
    # Verify flags are in CSV
    with open(cleaned_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert rows[0]['flags'] == '{"test": "flag"}'

def test_save_raw_and_cleaned_data_complete_pipeline(temp_project_root):
    """Test the complete pipeline from raw to cleaned data."""
    # Create mock raw records
    raw_records = [
        KnotRecord(
            knot_id="3_1",
            crossing_number=3,
            braid_index=2,
            hyperbolic_volume=0.533349,
            is_alternating=True,
            dt_code="4 -2",
            braid_word="s1 s1"
        )
    ]
    
    saver = DataSaver(temp_project_root)
    
    # Run complete pipeline
    raw_path, cleaned_path = saver.save_raw_and_cleaned_data(raw_records)
    
    # Verify both files exist
    assert raw_path.exists()
    assert cleaned_path.exists()
    
    # Verify raw is JSON
    with open(raw_path, 'r') as f:
        raw_data = json.load(f)
    assert isinstance(raw_data, list)
    
    # Verify cleaned is CSV
    with open(cleaned_path, 'r') as f:
        cleaned_data = list(csv.DictReader(f))
    assert isinstance(cleaned_data, list)

def test_save_raw_data_empty_list(temp_project_root):
    """Test that save_raw_data handles empty record list."""
    saver = DataSaver(temp_project_root)
    
    raw_path = saver.save_raw_data([])
    
    assert raw_path.exists()
    with open(raw_path, 'r') as f:
        data = json.load(f)
    assert data == []

def test_save_cleaned_data_empty_list(temp_project_root):
    """Test that save_cleaned_data handles empty record list."""
    saver = DataSaver(temp_project_root)
    
    cleaned_path = saver.save_cleaned_data([])
    
    assert cleaned_path.exists()
    with open(cleaned_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 0
    
    # Header should still exist
    with open(cleaned_path, 'r') as f:
        header = f.readline()
    assert 'knot_id' in header
    assert 'crossing_number' in header
