"""
Unit tests for the synthetic dataset generator (T026).
Verifies that the generator produces at least 10,000 records with both binary and continuous outcomes.
"""
import csv
import json
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    MIN_RECORDS
)
from code.src.config import set_rng_seed

@pytest.fixture
def seed():
    set_rng_seed(42)
    return 42

def test_generate_synthetic_dataset_count(seed):
    """Test that the generator produces at least 10,000 records."""
    records = generate_synthetic_dataset(MIN_RECORDS)
    assert len(records) >= MIN_RECORDS, f"Expected at least {MIN_RECORDS} records, got {len(records)}"

def test_generate_synthetic_dataset_outcome_types(seed):
    """Test that both binary and continuous outcomes are present."""
    records = generate_synthetic_dataset(MIN_RECORDS)
    binary_count, continuous_count = verify_outcome_types(records)
    
    assert binary_count > 0, "No binary outcomes found"
    assert continuous_count > 0, "No continuous outcomes found"
    assert binary_count + continuous_count == len(records), "Record count mismatch"

def test_write_csv_output(seed, tmp_path):
    """Test CSV output generation."""
    records = generate_synthetic_dataset(100)
    csv_path = tmp_path / "test_output.csv"
    
    write_csv_output(records, csv_path)
    
    assert csv_path.exists(), "CSV file not created"
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == len(records), "CSV row count mismatch"
    assert "outcome_type" in rows[0], "Missing outcome_type column"

def test_write_json_output(seed, tmp_path):
    """Test JSON output generation."""
    records = generate_synthetic_dataset(100)
    json_path = tmp_path / "test_output.json"
    
    write_json_output(records, json_path)
    
    assert json_path.exists(), "JSON file not created"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        loaded_records = json.load(f)
    
    assert len(loaded_records) == len(records), "JSON record count mismatch"

def test_verify_outcome_types_raises_on_missing_binary(seed):
    """Test that verify_outcome_types raises if binary outcomes are missing."""
    # Create a fake dataset with only continuous outcomes
    fake_records = [{"outcome_type": "continuous", "is_binary": False} for _ in range(10)]
    
    with pytest.raises(ValueError, match="No binary outcomes"):
        verify_outcome_types(fake_records)

def test_verify_outcome_types_raises_on_missing_continuous(seed):
    """Test that verify_outcome_types raises if continuous outcomes are missing."""
    # Create a fake dataset with only binary outcomes
    fake_records = [{"outcome_type": "binary", "is_binary": True} for _ in range(10)]
    
    with pytest.raises(ValueError, match="No continuous outcomes"):
        verify_outcome_types(fake_records)

def test_synthetic_data_structure(seed):
    """Test that generated records have the expected structure."""
    records = generate_synthetic_dataset(10)
    
    required_fields = [
        "id", "domain", "year", "outcome_type", "n_control", "n_treatment",
        "p_value", "effect_size", "inconsistent"
    ]
    
    for record in records:
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
        
        # Validate types
        assert isinstance(record["n_control"], int), "n_control must be int"
        assert isinstance(record["n_treatment"], int), "n_treatment must be int"
        assert 0.0 <= record["p_value"] <= 1.0, "p_value must be in [0, 1]"
        assert record["domain"] in ["tech", "finance", "health", "retail", "education"]
        assert 2018 <= record["year"] <= 2024
