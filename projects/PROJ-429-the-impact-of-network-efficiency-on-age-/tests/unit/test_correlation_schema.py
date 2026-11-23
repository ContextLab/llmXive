"""
Unit tests for the correlation result schema validation logic.
"""
import pytest
import json
import tempfile
import csv
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validate_correlation_schema import validate_row, load_schema

def test_validate_row_valid():
    schema = {
        "required": ["metric_name", "outcome", "spearman_r", "p_value", "p_adjusted", "n", "trace_id"],
        "properties": {
            "metric_name": {"type": "string"},
            "outcome": {"type": "string"},
            "spearman_r": {"type": "number"},
            "p_value": {"type": "number"},
            "p_adjusted": {"type": "number"},
            "n": {"type": "integer"},
            "trace_id": {"type": "string", "pattern": "^[a-f0-9]{64}$"}
        }
    }
    valid_row = {
        "metric_name": "global_efficiency",
        "outcome": "age",
        "spearman_r": "-0.45",
        "p_value": "0.001",
        "p_adjusted": "0.005",
        "n": "120",
        "trace_id": "a" * 64
    }
    errors = validate_row(valid_row, schema)
    assert len(errors) == 0

def test_validate_row_missing_required():
    schema = {
        "required": ["metric_name", "n"],
        "properties": {
            "metric_name": {"type": "string"},
            "n": {"type": "integer"}
        }
    }
    invalid_row = {
        "metric_name": "test"
        # missing 'n'
    }
    errors = validate_row(invalid_row, schema)
    assert len(errors) > 0
    assert any("n" in e for e in errors)

def test_validate_row_wrong_type():
    schema = {
        "required": ["n"],
        "properties": {
            "n": {"type": "integer"}
        }
    }
    invalid_row = {
        "n": "not_a_number"
    }
    errors = validate_row(invalid_row, schema)
    assert len(errors) > 0
    assert any("integer" in e for e in errors)

def test_validate_row_pattern_fail():
    schema = {
        "required": ["trace_id"],
        "properties": {
            "trace_id": {"type": "string", "pattern": "^[a-f0-9]{64}$"}
        }
    }
    invalid_row = {
        "trace_id": "short"
    }
    errors = validate_row(invalid_row, schema)
    assert len(errors) > 0
    assert any("pattern" in e for e in errors)