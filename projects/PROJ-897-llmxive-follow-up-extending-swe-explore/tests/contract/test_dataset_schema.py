"""
Contract test for the dataset schema (T007).
Verifies that the generated JSONL files conform to the expected schema defined in T004.
"""
import json
import pytest
from pathlib import Path

from utils.schemas import load_schema
from utils.validation import validate_record_against_schema

# Schema file path relative to project root
SCHEMA_PATH = Path("specs/001-llmxive-follow-up-extending-swe-explore/contracts/dataset_schema.yaml")

def load_jsonl(path: Path):
    """Helper to load JSONL file."""
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

def test_hard_subset_schema_conformance():
    """
    Test that a sample hard_subset.jsonl record conforms to the dataset schema.
    This validates the structure expected from T012 (Filter Hard Subset).
    """
    schema = load_schema(SCHEMA_PATH)
    
    # Sample record matching T012 output expectations:
    # issue_id, initial_coverage, ground_truth_lines, original_hash, patch_hash, code, is_synthetic
    sample_record = {
        "issue_id": "SWE-bench_test_123",
        "initial_coverage": 0.15,
        "ground_truth_lines": [10, 11, 12],
        "original_hash": "abc123def456",
        "patch_hash": "def456abc123",
        "code": "def calculate(x):\n    return x * 2",
        "is_synthetic": False,
        "problem_statement": "Fix the calculation function",
        "repo": "test/repo",
        "instance_id": "test_123"
    }

    try:
        is_valid = validate_record_against_schema(sample_record, schema)
        assert is_valid, "Hard subset sample record failed schema validation"
    except Exception as e:
        pytest.fail(f"Schema validation failed for hard subset: {e}")

def test_synthetic_issues_schema_conformance():
    """
    Test that a sample synthetic_issues.jsonl record conforms to the dataset schema.
    This validates the structure expected from T013 (Generate Synthetic Ambiguous Issues).
    """
    schema = load_schema(SCHEMA_PATH)
    
    # Sample record matching T013 output expectations:
    sample_record = {
        "issue_id": "synthetic_test_456",
        "initial_coverage": 0.20,
        "ground_truth_lines": [5, 6],
        "original_code_hash": "xyz789",
        "mutation_type": "var_rename",
        "code": "arg_0 = 1\nresult = arg_0 * 2",
        "is_synthetic": True,
        "problem_statement": "Fix the calculation function",
        "repo": "test/repo",
        "instance_id": "synthetic_456",
        "mutation_params": {
            "renamed_vars": ["x", "y"],
            "removed_comments": True
        }
    }

    try:
        is_valid = validate_record_against_schema(sample_record, schema)
        assert is_valid, "Synthetic issues sample record failed schema validation"
    except Exception as e:
        pytest.fail(f"Schema validation failed for synthetic issues: {e}")

def test_ground_truth_derived_schema_conformance():
    """
    Test that a sample derived ground truth record conforms to the dataset schema.
    This validates the structure expected from T011 (Implement Ground Truth Derivation).
    """
    schema = load_schema(SCHEMA_PATH)
    
    sample_record = {
        "issue_id": "gt_derived_789",
        "initial_coverage": 0.05,
        "ground_truth_lines": [1, 2, 3, 4, 5],
        "original_hash": "hash123",
        "patch_hash": "patch456",
        "code": "print('test')",
        "is_synthetic": False,
        "problem_statement": "Test problem",
        "repo": "test/repo",
        "instance_id": "gt_789",
        "derived_from": "bench.final.public"
    }

    try:
        is_valid = validate_record_against_schema(sample_record, schema)
        assert is_valid, "Ground truth derived sample record failed schema validation"
    except Exception as e:
        pytest.fail(f"Schema validation failed for ground truth derived: {e}")