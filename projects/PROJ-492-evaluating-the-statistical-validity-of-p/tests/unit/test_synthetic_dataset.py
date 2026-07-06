"""
Unit tests for synthetic dataset generator (T026).
Verifies FR-030 requirements: >= 10,000 records, both outcome types present.
"""

import pytest
import json
import csv
from pathlib import Path
import sys

# Add code root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds,
    generate_binary_outcome,
    generate_continuous_outcome
)

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    return tmp_path / "synthetic_output"

def test_minimum_record_count():
    """Test that at least 10,000 records are generated."""
    records = generate_synthetic_dataset(total_records=10000, output_dir=None)
    assert len(records) >= 10000, f"Expected >= 10000 records, got {len(records)}"

def test_both_outcome_types_present():
    """Test that both binary and continuous outcomes are generated."""
    records = generate_synthetic_dataset(total_records=10000, output_dir=None)
    binary_count, continuous_count, both_present = verify_outcome_types(records)
    
    assert binary_count > 0, "No binary outcomes generated"
    assert continuous_count > 0, "No continuous outcomes generated"
    assert both_present, "Both outcome types not present"

def test_binary_outcome_structure():
    """Test binary outcome record structure."""
    set_all_seeds()
    record = generate_binary_outcome(
        n_control=1000,
        n_treatment=1000,
        baseline_rate=0.2,
        effect_size=0.1,
        inject_inconsistency=False
    )
    
    required_fields = [
        "n_control", "n_treatment", "x_control", "x_treatment",
        "rate_control", "rate_treatment", "true_p_value", 
        "reported_p_value", "outcome_type", "is_inconsistent"
    ]
    
    for field in required_fields:
        assert field in record, f"Missing field: {field}"
    
    assert record["outcome_type"] == "binary"
    assert isinstance(record["n_control"], int)
    assert 0 <= record["rate_control"] <= 1

def test_continuous_outcome_structure():
    """Test continuous outcome record structure."""
    set_all_seeds()
    record = generate_continuous_outcome(
        n_control=1000,
        n_treatment=1000,
        baseline_mean=50.0,
        baseline_std=10.0,
        effect_size=0.1,
        inject_inconsistency=False
    )
    
    required_fields = [
        "n_control", "n_treatment", "mean_control", "mean_treatment",
        "std_control", "std_treatment", "true_p_value",
        "reported_p_value", "outcome_type", "is_inconsistent"
    ]
    
    for field in required_fields:
        assert field in record, f"Missing field: {field}"
    
    assert record["outcome_type"] == "continuous"

def test_csv_output_creation(temp_output_dir):
    """Test that CSV output file is created correctly."""
    records = generate_synthetic_dataset(
        total_records=100, 
        output_dir=temp_output_dir
    )
    
    csv_path = temp_output_dir / "synthetic_summaries.csv"
    assert csv_path.exists(), "CSV file not created"
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 100, f"Expected 100 rows, got {len(rows)}"

def test_json_output_creation(temp_output_dir):
    """Test that JSON output file is created correctly."""
    records = generate_synthetic_dataset(
        total_records=100, 
        output_dir=temp_output_dir
    )
    
    json_path = temp_output_dir / "synthetic_summaries.json"
    assert json_path.exists(), "JSON file not created"
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    assert isinstance(data, list)
    assert len(data) == 100

def test_metadata_creation(temp_output_dir):
    """Test that metadata file is created with correct content."""
    records = generate_synthetic_dataset(
        total_records=100, 
        output_dir=temp_output_dir
    )
    
    meta_path = temp_output_dir / "synthetic_metadata.json"
    assert meta_path.exists(), "Metadata file not created"
    
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    
    assert "total_records" in meta
    assert "binary_count" in meta
    assert "continuous_count" in meta
    assert meta["total_records"] == 100
    assert meta["both_types_present"] is True

def test_inconsistency_injection():
    """Test that inconsistency injection works."""
    set_all_seeds()
    consistent_records = [
        generate_binary_outcome(1000, 1000, 0.2, 0.1, False) 
        for _ in range(20)
    ]
    inconsistent_records = [
        generate_binary_outcome(1000, 1000, 0.2, 0.1, True) 
        for _ in range(20)
    ]
    
    # Consistent should have matching true/reported p-values (approx)
    for rec in consistent_records:
        assert abs(rec["true_p_value"] - rec["reported_p_value"]) < 0.01
    
    # Inconsistent should often have mismatches
    mismatch_count = 0
    for rec in inconsistent_records:
        if abs(rec["true_p_value"] - rec["reported_p_value"]) > 0.01:
            mismatch_count += 1
    
    # At least 50% should show inconsistency
    assert mismatch_count >= 10, f"Expected >= 10 inconsistent records, got {mismatch_count}"
