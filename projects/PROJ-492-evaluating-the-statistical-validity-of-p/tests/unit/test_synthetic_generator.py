"""
Unit tests for synthetic dataset generator (T026).
Verifies that the generator produces valid output with both outcome types.
"""

import csv
import json
import tempfile
from pathlib import Path
import pytest

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    generate_binary_outcome,
    generate_continuous_outcome,
    set_all_seeds
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_generate_binary_outcome():
    """Test binary outcome generation produces valid data."""
    result = generate_binary_outcome(
        n_control=1000,
        n_treatment=1000,
        baseline_rate=0.1,
        effect_size=0.05,
        seed=42
    )
    
    assert result["outcome_type"] == "binary"
    assert result["n_control"] == 1000
    assert result["n_treatment"] == 1000
    assert 0 <= result["n_control_success"] <= result["n_control"]
    assert 0 <= result["n_treatment_success"] <= result["n_treatment"]
    assert 0 <= result["p_control"] <= 1
    assert 0 <= result["p_treatment"] <= 1
    assert 0 <= result["p_value"] <= 1
    assert "ground_truth_baseline_rate" in result
    assert "ground_truth_treatment_rate" in result

def test_generate_continuous_outcome():
    """Test continuous outcome generation produces valid data."""
    result = generate_continuous_outcome(
        n_control=1000,
        n_treatment=1000,
        baseline_mean=50,
        baseline_std=10,
        effect_size=0.5,
        seed=42
    )
    
    assert result["outcome_type"] == "continuous"
    assert result["n_control"] == 1000
    assert result["n_treatment"] == 1000
    assert result["mean_control"] > 0
    assert result["mean_treatment"] > 0
    assert result["std_control"] > 0
    assert result["std_treatment"] > 0
    assert 0 <= result["p_value"] <= 1
    assert "ground_truth_baseline_mean" in result
    assert "ground_truth_effect_size" in result

def test_generate_synthetic_dataset_minimum_count(temp_output_dir):
    """Test that dataset generation produces at least 10,000 records."""
    output_csv = temp_output_dir / "test_synthetic.csv"
    output_json = temp_output_dir / "test_ground_truth.json"
    
    csv_records, ground_truth_records = generate_synthetic_dataset(
        n_summaries=10000,
        seed=42,
        output_csv=output_csv,
        output_json=output_json
    )
    
    assert len(csv_records) >= 10000
    assert len(ground_truth_records) >= 10000

def test_generate_synthetic_dataset_both_outcome_types(temp_output_dir):
    """Test that dataset contains both binary and continuous outcomes."""
    output_csv = temp_output_dir / "test_synthetic.csv"
    output_json = temp_output_dir / "test_ground_truth.json"
    
    csv_records, ground_truth_records = generate_synthetic_dataset(
        n_summaries=10000,
        seed=42,
        output_csv=output_csv,
        output_json=output_json
    )
    
    binary_count, continuous_count, is_valid = verify_outcome_types(csv_records)
    
    assert is_valid, "Dataset must contain both binary and continuous outcomes"
    assert binary_count > 0, "Must have at least one binary outcome"
    assert continuous_count > 0, "Must have at least one continuous outcome"
    
    # Verify proportions (approximately 60% binary, 40% continuous)
    assert 0.5 <= binary_count / len(csv_records) <= 0.7
    assert 0.3 <= continuous_count / len(csv_records) <= 0.5

def test_csv_output_format(temp_output_dir):
    """Test CSV output has correct format and columns."""
    output_csv = temp_output_dir / "test_synthetic.csv"
    output_json = temp_output_dir / "test_ground_truth.json"
    
    generate_synthetic_dataset(
        n_summaries=100,
        seed=42,
        output_csv=output_csv,
        output_json=output_json
    )
    
    assert output_csv.exists(), "CSV output file must exist"
    
    with open(output_csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 100
    
    # Check required columns
    required_columns = [
        "test_id", "outcome_type", "domain", "year",
        "n_control", "n_treatment", "p_value", "is_significant"
    ]
    
    for col in required_columns:
        assert col in reader.fieldnames, f"Missing column: {col}"

def test_json_output_format(temp_output_dir):
    """Test JSON output has correct format and metadata."""
    output_csv = temp_output_dir / "test_synthetic.csv"
    output_json = temp_output_dir / "test_ground_truth.json"
    
    generate_synthetic_dataset(
        n_summaries=100,
        seed=42,
        output_csv=output_csv,
        output_json=output_json
    )
    
    assert output_json.exists(), "JSON output file must exist"
    
    with open(output_json, 'r') as f:
        data = json.load(f)
    
    assert "metadata" in data
    assert "records" in data
    assert data["metadata"]["total_records"] == 100
    assert "binary_count" in data["metadata"]
    assert "continuous_count" in data["metadata"]
    assert data["metadata"]["binary_count"] + data["metadata"]["continuous_count"] == 100

def test_reproducibility(temp_output_dir):
    """Test that same seed produces same results."""
    output_csv1 = temp_output_dir / "test1.csv"
    output_json1 = temp_output_dir / "test1.json"
    output_csv2 = temp_output_dir / "test2.csv"
    output_json2 = temp_output_dir / "test2.json"
    
    generate_synthetic_dataset(n_summaries=100, seed=42, output_csv=output_csv1, output_json=output_json1)
    generate_synthetic_dataset(n_summaries=100, seed=42, output_csv=output_csv2, output_json=output_json2)
    
    with open(output_csv1, 'r') as f1, open(output_csv2, 'r') as f2:
        content1 = f1.read()
        content2 = f2.read()
    
    assert content1 == content2, "Same seed should produce identical output"

def test_verify_outcome_types_function():
    """Test the verify_outcome_types function."""
    # Test with mixed outcomes
    mixed_records = [
        {"outcome_type": "binary"},
        {"outcome_type": "continuous"},
        {"outcome_type": "binary"}
    ]
    binary, continuous, valid = verify_outcome_types(mixed_records)
    assert binary == 2
    assert continuous == 1
    assert valid is True
    
    # Test with only binary
    binary_only = [{"outcome_type": "binary"}]
    binary, continuous, valid = verify_outcome_types(binary_only)
    assert valid is False
    
    # Test with only continuous
    continuous_only = [{"outcome_type": "continuous"}]
    binary, continuous, valid = verify_outcome_types(continuous_only)
    assert valid is False

def test_sample_size_distribution(temp_output_dir):
    """Test that sample sizes follow expected distribution."""
    output_csv = temp_output_dir / "test_synthetic.csv"
    output_json = temp_output_dir / "test_ground_truth.json"
    
    csv_records, _ = generate_synthetic_dataset(
        n_summaries=1000,
        seed=42,
        output_csv=output_csv,
        output_json=output_json
    )
    
    sample_sizes = [r["n_control"] for r in csv_records]
    
    assert all(50 <= s <= 10000 for s in sample_sizes), "Sample sizes must be within valid range"
    assert min(sample_sizes) >= 50
    assert max(sample_sizes) <= 10000
