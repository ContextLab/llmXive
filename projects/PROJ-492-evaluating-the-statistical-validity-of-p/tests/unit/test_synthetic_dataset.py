import csv
import json
import os
import pytest
from pathlib import Path

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    write_csv_output,
    write_json_output,
    verify_outcome_types,
    main
)

# Test directories
TEST_OUTPUT_DIR = Path("data/synthetic_test")
TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@pytest.fixture
def synthetic_data():
    """Generate synthetic data for testing."""
    summaries, ground_truth = generate_synthetic_dataset(
        n_records=100,
        seed=42,
        binary_ratio=0.5
    )
    return summaries, ground_truth

def test_generate_synthetic_dataset_count(synthetic_data):
    """Test that the correct number of records is generated."""
    summaries, _ = synthetic_data
    assert len(summaries) == 100

def test_generate_synthetic_dataset_both_types(synthetic_data):
    """Test that both binary and continuous outcomes are present."""
    summaries, _ = synthetic_data
    binary_count = sum(1 for s in summaries if s.get("outcome_type") == "binary")
    continuous_count = sum(1 for s in summaries if s.get("outcome_type") == "continuous")
    
    assert binary_count > 0, "No binary outcomes generated"
    assert continuous_count > 0, "No continuous outcomes generated"
    assert binary_count + continuous_count == len(summaries)

def test_verify_outcome_types(synthetic_data):
    """Test the outcome type verification function."""
    summaries, _ = synthetic_data
    binary_count, continuous_count = verify_outcome_types(summaries)
    
    assert binary_count > 0
    assert continuous_count > 0

def test_csv_output_format(synthetic_data):
    """Test that CSV output has correct format and content."""
    summaries, _ = synthetic_data
    output_path = TEST_OUTPUT_DIR / "test_synthetic.csv"
    
    write_csv_output(summaries, output_path)
    
    assert output_path.exists(), "CSV file not created"
    
    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == len(summaries), "Row count mismatch"
    
    # Check required columns exist
    required_columns = ["outcome_type", "n_control", "n_treatment", "p_value_reported"]
    for col in required_columns:
        assert col in reader.fieldnames, f"Missing column: {col}"

def test_json_output_format(synthetic_data):
    """Test that JSON output has correct format and content."""
    _, ground_truth = synthetic_data
    output_path = TEST_OUTPUT_DIR / "test_ground_truth.json"
    
    write_json_output(ground_truth, output_path)
    
    assert output_path.exists(), "JSON file not created"
    
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert len(data) == len(ground_truth), "Record count mismatch"
    
    # Check required fields in ground truth
    required_fields = ["id", "outcome_type", "true_p_value", "is_consistent"]
    for record in data:
        for field in required_fields:
            assert field in record, f"Missing field in ground truth: {field}"

def test_reproducibility():
    """Test that generation is reproducible with same seed."""
    summaries1, _ = generate_synthetic_dataset(n_records=50, seed=123)
    summaries2, _ = generate_synthetic_dataset(n_records=50, seed=123)
    
    # Compare key fields
    for s1, s2 in zip(summaries1, summaries2):
        assert s1["outcome_type"] == s2["outcome_type"]
        assert s1["n_control"] == s2["n_control"]
        assert s1["n_treatment"] == s2["n_treatment"]
        assert s1["p_value_reported"] == s2["p_value_reported"]

def test_minimum_record_count():
    """Test that we can generate at least 10,000 records."""
    summaries, _ = generate_synthetic_dataset(n_records=10000, seed=42)
    assert len(summaries) >= 10000
    
    # Verify both types present
    binary_count, continuous_count = verify_outcome_types(summaries)
    assert binary_count >= 1
    assert continuous_count >= 1

def cleanup_test_files():
    """Clean up test output files."""
    import shutil
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)

def teardown_module(module):
    """Clean up after all tests."""
    cleanup_test_files()
