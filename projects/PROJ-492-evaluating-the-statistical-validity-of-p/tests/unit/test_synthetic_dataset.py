import pytest
import csv
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    write_csv_output,
    write_json_output,
    verify_outcome_types,
    set_all_seeds
)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / 'synthetic'
    output_dir.mkdir()
    return output_dir

def test_generate_synthetic_dataset_count():
    """Test that the generator produces the requested number of records."""
    records = generate_synthetic_dataset(num_records=100, seed=42)
    assert len(records) == 100

def test_generate_synthetic_dataset_both_outcomes():
    """Test that both binary and continuous outcomes are generated."""
    records = generate_synthetic_dataset(num_records=1000, binary_ratio=0.5, seed=42)
    
    binary_count = sum(1 for r in records if r['outcome_type'] == 'binary')
    continuous_count = sum(1 for r in records if r['outcome_type'] == 'continuous')
    
    assert binary_count > 0, "No binary outcomes generated"
    assert continuous_count > 0, "No continuous outcomes generated"
    assert binary_count + continuous_count == len(records)

def test_verify_outcome_types_success():
    """Test verification passes when both types present."""
    records = generate_synthetic_dataset(num_records=100, binary_ratio=0.5, seed=42)
    success, counts = verify_outcome_types(records)
    
    assert success is True
    assert counts['binary'] > 0
    assert counts['continuous'] > 0

def test_verify_outcome_types_failure():
    """Test verification fails when one type missing."""
    # Create a list with only binary outcomes
    records = generate_synthetic_dataset(num_records=100, binary_ratio=1.0, seed=42)
    success, counts = verify_outcome_types(records)
    
    assert success is False
    assert counts['continuous'] == 0

def test_write_csv_output(temp_output_dir):
    """Test CSV output file is created and contains data."""
    records = generate_synthetic_dataset(num_records=100, seed=42)
    csv_path = temp_output_dir / 'test.csv'
    
    write_csv_output(records, csv_path)
    
    assert csv_path.exists()
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 100
    assert 'id' in rows[0]
    assert 'outcome_type' in rows[0]
    assert 'reported_p_value' in rows[0]

def test_write_json_output(temp_output_dir):
    """Test JSON ground truth file is created and contains metadata."""
    records = generate_synthetic_dataset(num_records=100, seed=42)
    json_path = temp_output_dir / 'test.json'
    
    write_json_output(records, json_path)
    
    assert json_path.exists()
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert 'metadata' in data
    assert data['metadata']['total_records'] == 100
    assert 'binary_count' in data['metadata']
    assert 'continuous_count' in data['metadata']
    assert data['metadata']['binary_count'] > 0
    assert data['metadata']['continuous_count'] > 0

def test_large_dataset_generation(tmp_path):
    """Test generation of 10,000+ records as required by T026."""
    output_dir = tmp_path / 'synthetic'
    output_dir.mkdir()
    
    records = generate_synthetic_dataset(num_records=10000, seed=42)
    
    assert len(records) >= 10000
    
    csv_path = output_dir / 'synthetic_validation.csv'
    json_path = output_dir / 'synthetic_ground_truth.json'
    
    write_csv_output(records, csv_path)
    write_json_output(records, json_path)
    
    assert csv_path.exists()
    assert json_path.exists()
    
    # Verify content
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        csv_count = sum(1 for _ in reader)
    
    assert csv_count >= 10000
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert data['metadata']['total_records'] >= 10000
    assert data['metadata']['binary_count'] > 0
    assert data['metadata']['continuous_count'] > 0

def test_data_consistency_flag():
    """Test that the is_consistent flag is properly set."""
    records = generate_synthetic_dataset(num_records=1000, inconsistency_rate=0.2, seed=42)
    
    consistent_count = sum(1 for r in records if r['is_consistent'])
    inconsistent_count = sum(1 for r in records if not r['is_consistent'])
    
    # Check that we have both consistent and inconsistent records
    assert consistent_count > 0
    assert inconsistent_count > 0
    
    # Check approximate rate (allowing for randomness)
    expected_inconsistent = 1000 * 0.2
    assert 0.15 * 1000 <= inconsistent_count <= 0.25 * 1000

def test_required_fields_present():
    """Test that all required fields are present in generated records."""
    records = generate_synthetic_dataset(num_records=10, seed=42)
    
    required_fields = [
        'id', 'outcome_type', 'domain', 'year',
        'n_control', 'n_treatment', 'obs_effect_size',
        'reported_p_value', 'is_consistent'
    ]
    
    for record in records:
        for field in required_fields:
            assert field in record, f"Missing field: {field}"
    
    # Check binary-specific fields
    binary_records = [r for r in records if r['outcome_type'] == 'binary']
    if binary_records:
        binary_fields = ['successes_control', 'successes_treatment', 'obs_control_rate', 'obs_treatment_rate']
        for field in binary_fields:
            assert field in binary_records[0], f"Missing binary field: {field}"
    
    # Check continuous-specific fields
    continuous_records = [r for r in records if r['outcome_type'] == 'continuous']
    if continuous_records:
        continuous_fields = ['obs_mean_control', 'obs_mean_treatment', 'obs_std_control', 'obs_std_treatment']
        for field in continuous_fields:
            assert field in continuous_records[0], f"Missing continuous field: {field}"