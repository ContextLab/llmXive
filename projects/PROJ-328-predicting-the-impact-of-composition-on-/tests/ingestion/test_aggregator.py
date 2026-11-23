"""
Tests for the LiteratureAggregator in code/ingestion/aggregator.py.
"""

import os
import json
import csv
import hashlib
import tempfile
import pytest
from pathlib import Path

from ingestion.aggregator import LiteratureAggregator


@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory for raw data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        raw_dir.mkdir()
        yield raw_dir


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return [
        {"element": "Sn", "percentage": 63.0, "hardness_hv": 15.5},
        {"element": "Ag", "percentage": 37.0, "hardness_hv": 18.2}
    ]


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return [
        {"element": "Pb", "percentage": 37.0, "hardness_hv": 12.1},
        {"element": "Sn", "percentage": 63.0, "hardness_hv": 14.5}
    ]


def test_calculate_sha256(temp_raw_dir, sample_json_data):
    """Test SHA256 checksum calculation."""
    aggregator = LiteratureAggregator(raw_dir=temp_raw_dir)
    
    # Write a test file
    test_file = temp_raw_dir / "test.json"
    with open(test_file, "w") as f:
        json.dump(sample_json_data, f)
    
    checksum = aggregator._calculate_sha256(test_file)
    
    # Verify checksum is a valid hex string
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)


def test_write_json_raw(temp_raw_dir, sample_json_data):
    """Test writing JSON raw data."""
    aggregator = LiteratureAggregator(raw_dir=temp_raw_dir)
    
    output_path = aggregator._write_json_raw(sample_json_data, "test_raw.json")
    
    assert output_path.exists()
    assert output_path.name == "test_raw.json"
    
    with open(output_path, "r") as f:
        loaded_data = json.load(f)
    
    assert loaded_data == sample_json_data


def test_write_csv_raw(temp_raw_dir, sample_csv_data):
    """Test writing CSV raw data."""
    aggregator = LiteratureAggregator(raw_dir=temp_raw_dir)
    
    output_path = aggregator._write_csv_raw(sample_csv_data, "test_raw.csv")
    
    assert output_path.exists()
    assert output_path.name == "test_raw.csv"
    
    with open(output_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == len(sample_csv_data)
    assert rows[0] == sample_csv_data[0]


def test_add_checksum(temp_raw_dir, sample_json_data):
    """Test adding checksums."""
    aggregator = LiteratureAggregator(raw_dir=temp_raw_dir)
    
    # Write a file
    output_path = aggregator._write_json_raw(sample_json_data, "test.json")
    
    # Add checksum
    aggregator._add_checksum(output_path)
    
    assert len(aggregator.checksums) == 1
    assert aggregator.checksums[0]["filename"] == "test.json"
    assert len(aggregator.checksums[0]["checksum"]) == 64


def test_write_checksums(temp_raw_dir, sample_json_data):
    """Test writing checksums to file."""
    aggregator = LiteratureAggregator(raw_dir=temp_raw_dir)
    
    # Write a file and add checksum
    output_path = aggregator._write_json_raw(sample_json_data, "test.json")
    aggregator._add_checksum(output_path)
    
    # Write checksums
    aggregator._write_checksums()
    
    checksum_file = temp_raw_dir.parent / "checksums.txt"
    assert checksum_file.exists()
    
    with open(checksum_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 1
    assert "test.json" in lines[0]
    assert len(lines[0].split()[0]) == 64  # checksum length


def test_aggregate_api_data(temp_raw_dir, sample_json_data):
    """Test aggregating API data."""
    aggregator = LiteratureAggregator(raw_dir=temp_raw_dir)
    
    aggregator.aggregate_api_data(
        mp_data=sample_json_data,
        openalloy_data=sample_json_data
    )
    
    # Check files were created
    assert (temp_raw_dir / "raw_mp.json").exists()
    assert (temp_raw_dir / "raw_openalloy.json").exists()
    
    # Check checksums were recorded
    assert len(aggregator.checksums) == 2


def test_aggregate_literature_data(temp_raw_dir, sample_csv_data):
    """Test aggregating literature data."""
    aggregator = LiteratureAggregator(raw_dir=temp_raw_dir)
    
    aggregator.aggregate_literature_data(
        lit_data=sample_csv_data,
        slr_data=sample_csv_data
    )
    
    # Check files were created
    assert (temp_raw_dir / "raw_lit.csv").exists()
    assert (temp_raw_dir / "raw_slr.csv").exists()
    
    # Check checksums were recorded
    assert len(aggregator.checksums) == 2
