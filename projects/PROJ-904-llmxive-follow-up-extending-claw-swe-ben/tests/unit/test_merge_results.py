"""
Unit tests for the merge_results module.
"""

import json
import csv
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
import os
# Ensure we can import from the code directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from analysis.merge_results import (
    validate_input_schema,
    validate_strategy_consistency,
    validate_model_sizes,
    aggregate_jsonl,
    compute_row_hash,
    execute_merge,
    MergedResultRow
)

# Sample valid record
VALID_RECORD = {
    "instance_id": "test-123",
    "model_size": "1B",
    "strategy": "baseline",
    "pass_at_1": 1,
    "execution_time": 12.5,
    "tokens_used": 100,
    "failure_mode": None,
    "context_lines": 2048
}

def test_validate_input_schema_valid():
    """Test that a valid record passes validation."""
    # Should not raise
    validate_input_schema(VALID_RECORD, "test.jsonl")

def test_validate_input_schema_invalid():
    """Test that a record with missing keys raises ValueError."""
    invalid_record = {"instance_id": "test-123"}
    with pytest.raises(ValueError) as excinfo:
        validate_input_schema(invalid_record, "test.jsonl")
    assert "missing keys" in str(excinfo.value)

def test_validate_strategy_consistency_valid():
    """Test that valid strategies pass."""
    records = [
        {"strategy": "baseline"},
        {"strategy": "tfidf"},
        {"strategy": "diff_aware"},
        {"strategy": "summarization"}
    ]
    # Should not raise
    validate_strategy_consistency(records)

def test_validate_strategy_consistency_invalid():
    """Test that invalid strategies trigger a warning (logged, not raised)."""
    records = [{"strategy": "invalid_strategy"}]
    # Should not raise, just log a warning
    validate_strategy_consistency(records)

def test_validate_model_sizes_valid():
    """Test that valid model sizes pass."""
    records = [
        {"model_size": "1B"},
        {"model_size": "7B"}
    ]
    validate_model_sizes(records)

def test_validate_model_sizes_invalid():
    """Test that invalid model sizes trigger a warning."""
    records = [{"model_size": "13B"}]
    validate_model_sizes(records)

def test_aggregate_jsonl(tmp_path):
    """Test reading and aggregating JSONL files."""
    # Create a temporary JSONL file
    input_file = tmp_path / "test.jsonl"
    with open(input_file, 'w') as f:
        json.dump(VALID_RECORD, f)
        f.write('\n')
        json.dump({**VALID_RECORD, "instance_id": "test-456"}, f)
        f.write('\n')

    records = aggregate_jsonl([input_file])

    assert len(records) == 2
    assert records[0]["instance_id"] == "test-123"
    assert records[1]["instance_id"] == "test-456"

def test_aggregate_jsonl_missing_file(tmp_path):
    """Test that aggregate_jsonl raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        aggregate_jsonl([tmp_path / "nonexistent.jsonl"])

def test_compute_row_hash():
    """Test that compute_row_hash returns a consistent hash."""
    record = {"a": 1, "b": 2}
    hash1 = compute_row_hash(record)
    hash2 = compute_row_hash(record)
    assert hash1 == hash2
    assert len(hash1) == 16  # Truncated SHA256

def test_execute_merge(tmp_path):
    """Test the full merge execution."""
    # Setup input files
    input1 = tmp_path / "baseline.jsonl"
    input2 = tmp_path / "hf_1b.jsonl"

    with open(input1, 'w') as f:
        json.dump(VALID_RECORD, f)
        f.write('\n')
    with open(input2, 'w') as f:
        json.dump({**VALID_RECORD, "model_size": "1B", "strategy": "tfidf"}, f)
        f.write('\n')

    output_file = tmp_path / "results.csv"

    execute_merge([input1, input2], output_file)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        # Check headers
        assert 'hash' in rows[0]
        assert 'instance_id' in rows[0]
        assert 'pass_at_1' in rows[0]