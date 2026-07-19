"""
Tests for the ingestion module.

These tests verify:
- Data loading and schema validation
- Missing data handling and exclusion logic
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv
import tempfile

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from ingest import (
    validate_schema,
    identify_primary_quality_dimension,
    load_and_align_data,
    print_summary,
    calculate_sha256
)

@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file with valid schema for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_id", "prompt", "image_url", "teacher_logits", "student_scores",
            "human_alignment", "human_realism", "human_aesthetics", "human_plausibility",
            "primary_dimension"
        ])
        writer.writerow([
            "1", "Test prompt 1", "http://example.com/1.jpg", "[0.1, 0.2, 0.3, 0.4]",
            "0.8", "0.9", "0.7", "0.85", "Alignment"
        ])
        writer.writerow([
            "2", "Test prompt 2", "http://example.com/2.jpg", "[0.2, 0.3, 0.4, 0.1]",
            "0.7", "", "0.6", "0.75", "Realism"
        ])
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

@pytest.fixture
def invalid_csv_file():
    """Create a temporary CSV file with invalid schema for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "prompt", "wrong_column"])
        writer.writerow(["1", "Test", "value"])
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_validate_schema_valid(sample_csv_file):
    """Test schema validation with a valid CSV file."""
    is_valid, missing = validate_schema(sample_csv_file)
    assert is_valid is True
    assert len(missing) == 0

def test_validate_schema_invalid(invalid_csv_file):
    """Test schema validation with an invalid CSV file."""
    is_valid, missing = validate_schema(invalid_csv_file)
    assert is_valid is False
    assert len(missing) > 0
    assert "human_alignment" in missing

def test_identify_primary_quality_dimension_valid():
    """Test primary dimension identification with valid input."""
    metadata = {"primary_dimension": "Aesthetics"}
    result = identify_primary_quality_dimension(metadata)
    assert result == "Aesthetics"

def test_identify_primary_quality_dimension_default():
    """Test primary dimension identification with missing field."""
    metadata = {}
    result = identify_primary_quality_dimension(metadata)
    assert result == "Alignment"

def test_identify_primary_quality_dimension_invalid():
    """Test primary dimension identification with invalid value."""
    metadata = {"primary_dimension": "InvalidDimension"}
    result = identify_primary_quality_dimension(metadata)
    assert result == "Alignment"  # Should default to Alignment

def test_load_and_align_data(sample_csv_file):
    """Test data loading and alignment."""
    data = load_and_align_data(sample_csv_file)
    assert len(data) == 2
    assert data[0]["sample_id"] == "1"
    assert data[1]["primary_dimension"] == "Realism"

def test_load_and_align_data_missing_values(sample_csv_file):
    """Test data loading with missing values."""
    data = load_and_align_data(sample_csv_file)
    assert len(data) == 2
    # Second row has missing human_realism
    assert data[1]["human_realism"] is None or data[1]["human_realism"] == ""

def test_print_summary(sample_csv_file, capsys):
    """Test summary printing functionality."""
    data = load_and_align_data(sample_csv_file)
    print_summary(data)
    
    captured = capsys.readouterr()
    assert "DATASET SUMMARY" in captured.out
    assert "Total samples:" in captured.out
    assert "Missing data counts:" in captured.out

def test_calculate_sha256(sample_csv_file):
    """Test SHA256 calculation."""
    checksum = calculate_sha256(sample_csv_file)
    assert checksum.startswith("sha256:")
    assert len(checksum) == 71  # sha256: + 64 hex chars

def test_load_and_align_data_chunking(sample_csv_file):
    """Test that chunking works correctly with small chunk size."""
    data = load_and_align_data(sample_csv_file, chunk_size=1)
    assert len(data) == 2
    assert data[0]["sample_id"] == "1"
    assert data[1]["sample_id"] == "2"

def test_load_and_align_data_empty_file():
    """Test loading an empty CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow([
            "sample_id", "prompt", "image_url", "teacher_logits", "student_scores",
            "human_alignment", "human_realism", "human_aesthetics", "human_plausibility",
            "primary_dimension"
        ])
        temp_path = f.name
    
    try:
        data = load_and_align_data(temp_path)
        assert len(data) == 0
    finally:
        os.unlink(temp_path)
