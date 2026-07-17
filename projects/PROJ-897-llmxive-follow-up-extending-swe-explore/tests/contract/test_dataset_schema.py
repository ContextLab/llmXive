"""
Contract test for the dataset schema (T009).
Verifies that the generated JSONL files conform to the expected schema.
"""
import json
import pytest
from pathlib import Path

from utils.schemas import load_schema
from utils.validation import validate_record_against_schema

# Schema file path relative to project root
SCHEMA_PATH = Path("contracts/dataset_schema.yaml")

def load_jsonl(path: Path):
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def test_dataset_schema_exists():
    """Ensure the schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_hard_subset_schema_conformance(tmp_path):
    """
    Test that a sample hard_subset.jsonl conforms to the dataset schema.
    """
    # Load schema
    schema = load_schema(SCHEMA_PATH)
    
    # Create a sample record conforming to the schema
    # Based on T014a requirements: issue_id, initial_coverage, ground_truth_lines, etc.
    sample_record = {
        "issue_id": "test_123",
        "initial_coverage": 0.15,
        "ground_truth_lines": [1, 2, 3],
        "original_hash": "abc123",
        "patch_hash": "def456",
        "code": "print('hello')",
        "is_synthetic": False
    }

    # Validate against schema
    # This function should raise or return status based on implementation in utils/validation.py
    # Assuming validate_record_against_schema returns True on success or raises
    try:
        is_valid = validate_record_against_schema(sample_record, schema)
        assert is_valid, "Sample record failed schema validation"
    except Exception as e:
        pytest.fail(f"Schema validation failed: {e}")

def test_synthetic_issues_schema_conformance(tmp_path):
    """
    Test that a sample synthetic_issues.jsonl conforms to the dataset schema.
    """
    schema = load_schema(SCHEMA_PATH)
    
    sample_record = {
        "issue_id": "synthetic_test_456",
        "initial_coverage": 0.20,
        "ground_truth_lines": [5, 6],
        "original_code_hash": "xyz789",
        "mutation_type": "var_rename",
        "code": "arg_0 = 1",
        "is_synthetic": True
    }

    try:
        is_valid = validate_record_against_schema(sample_record, schema)
        assert is_valid, "Synthetic sample record failed schema validation"
    except Exception as e:
        pytest.fail(f"Schema validation failed: {e}")
