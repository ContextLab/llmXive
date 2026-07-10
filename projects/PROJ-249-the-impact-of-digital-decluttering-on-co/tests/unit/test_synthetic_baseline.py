"""
Unit tests for synthetic baseline data generator (T017).

Tests verify:
1. Output file is created at correct path
2. CSV has correct columns
3. Participant IDs match P\\d{3} pattern
4. Values are within expected ranges
5. Timestamps are valid ISO format
"""
import os
import csv
import re
from pathlib import Path
import pytest

# Import the main function and constants
import code.validation.synthetic_baseline as synth_module

# Get the expected output path
EXPECTED_OUTPUT = synth_module.PROJECT_ROOT / "data" / "raw" / "synthetic_baseline.csv"

@pytest.fixture(scope="module")
def generated_data():
    """Generate data once for all tests in this module."""
    # Ensure the data directory exists
    synth_module.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run the generator
    synth_module.main()
    
    # Read and return the data
    if not EXPECTED_OUTPUT.exists():
        pytest.fail(f"Output file not created at {EXPECTED_OUTPUT}")
    
    with open(EXPECTED_OUTPUT, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    return data

def test_output_file_exists(generated_data):
    """Test that the output file is created."""
    assert EXPECTED_OUTPUT.exists(), f"Output file {EXPECTED_OUTPUT} was not created"
    assert EXPECTED_OUTPUT.stat().st_size > 0, "Output file is empty"

def test_csv_columns(generated_data):
    """Test that CSV has the required columns."""
    required_columns = {"participant_id", "metric_type", "value", "timestamp"}
    if generated_data:
        actual_columns = set(generated_data[0].keys())
        assert required_columns.issubset(actual_columns), \
            f"Missing columns. Expected: {required_columns}, Got: {actual_columns}"

def test_participant_id_format(generated_data):
    """Test that participant IDs match P\\d{3} pattern (FR-001)."""
    pattern = re.compile(r'^P\d{3}$')
    participant_ids = set(row['participant_id'] for row in generated_data)
    
    for pid in participant_ids:
        assert pattern.match(pid), f"Invalid participant ID format: {pid}"

def test_unique_participant_ids(generated_data):
    """Test that participant IDs are unique."""
    participant_ids = [row['participant_id'] for row in generated_data]
    assert len(participant_ids) == len(set(participant_ids)), \
        "Duplicate participant IDs found"

def test_value_ranges(generated_data):
    """Test that all values are within expected ranges."""
    # Define expected ranges (metric_name: (min, max))
    expected_ranges = {
        "sart_commission_errors": (0, 25),
        "sart_mean_rt": (200, 1500),
        "ospan_score": (0, 60),
        "pss10_total": (0, 40),
        "panas_positive": (10, 50),
        "panas_negative": (10, 50),
    }
    
    for row in generated_data:
        metric = row['metric_type']
        value = float(row['value'])
        
        if metric in expected_ranges:
            min_val, max_val = expected_ranges[metric]
            assert min_val <= value <= max_val, \
                f"Value {value} for {metric} out of range [{min_val}, {max_val}]"

def test_timestamp_format(generated_data):
    """Test that timestamps are valid ISO format."""
    from datetime import datetime
    
    for row in generated_data:
        timestamp_str = row['timestamp']
        try:
            # Try parsing as ISO format
            datetime.fromisoformat(timestamp_str)
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp_str}")

def test_expected_metrics_present(generated_data):
    """Test that all expected metrics are present in the data."""
    expected_metrics = {
        "sart_commission_errors",
        "sart_mean_rt", 
        "ospan_score",
        "pss10_total",
        "panas_positive",
        "panas_negative",
    }
    
    actual_metrics = set(row['metric_type'] for row in generated_data)
    
    assert expected_metrics.issubset(actual_metrics), \
        f"Missing metrics. Expected: {expected_metrics}, Got: {actual_metrics}"

def test_record_count(generated_data):
    """Test that the expected number of records is generated."""
    # NUM_PARTICIPANTS * NUM_METRICS
    expected_count = synth_module.NUM_PARTICIPANTS * len(synth_module.METRIC_CONFIGS)
    assert len(generated_data) == expected_count, \
        f"Expected {expected_count} records, got {len(generated_data)}"

def test_deterministic_generation():
    """Test that running the generator twice produces the same output."""
    # First run
    synth_module.main()
    with open(EXPECTED_OUTPUT, 'r') as f:
        first_run = f.read()
    
    # Second run (should be identical due to seed)
    synth_module.main()
    with open(EXPECTED_OUTPUT, 'r') as f:
        second_run = f.read()
    
    assert first_run == second_run, "Generator is not deterministic"