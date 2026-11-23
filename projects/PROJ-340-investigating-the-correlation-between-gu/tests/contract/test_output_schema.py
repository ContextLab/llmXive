"""
Contract test for correlation output schema.

Validates the structure of correlation results against the defined schema.
This test ensures that the pipeline's output matches the expected format
required by downstream consumers and reporting tools.
"""
import os
import json
import pytest
from pathlib import Path

# Path to the output file produced by the pipeline
OUTPUT_PATH = Path("data/results/correlation_matrix.json")

# Required fields as defined in the output schema (T008a)
REQUIRED_FIELDS = [
    "predictor",
    "outcome",
    "correlation",
    "p_value",
    "q_value",
    "method",
    "significant"
]

# Expected data types for numeric fields
NUMERIC_FIELDS = ["correlation", "p_value", "q_value"]


def test_correlation_output_exists():
    """Test that the correlation output file exists."""
    assert OUTPUT_PATH.exists(), f"Output file not found: {OUTPUT_PATH}"


def test_correlation_output_is_valid_json():
    """Test that the output file contains valid JSON."""
    try:
        with open(OUTPUT_PATH, 'r') as f:
            json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"Output file is not valid JSON: {e}")


def test_correlation_output_structure():
    """Test that the correlation output has the required top-level structure."""
    with open(OUTPUT_PATH, 'r') as f:
        results = json.load(f)

    # The output should be a list of correlation records
    assert isinstance(results, list), "Output must be a list of correlation records"


def test_correlation_record_fields():
    """Test that each correlation record contains all required fields."""
    with open(OUTPUT_PATH, 'r') as f:
        results = json.load(f)

    # Only check if there are records to validate
    if len(results) == 0:
        pytest.skip("No correlation records to validate (empty result set)")

    for i, record in enumerate(results):
        assert isinstance(record, dict), f"Record {i} is not a dictionary"
        for field in REQUIRED_FIELDS:
            assert field in record, f"Record {i} missing required field: {field}"


def test_correlation_record_types():
    """Test that numeric fields contain numeric values."""
    with open(OUTPUT_PATH, 'r') as f:
        results = json.load(f)

    if len(results) == 0:
        pytest.skip("No correlation records to validate (empty result set)")

    for i, record in enumerate(results):
        for field in NUMERIC_FIELDS:
            value = record.get(field)
            assert isinstance(value, (int, float)), \
                f"Record {i}, field '{field}' must be numeric, got {type(value)}"
            # Check for NaN or Inf
            import math
            if isinstance(value, float):
                assert not math.isnan(value), \
                    f"Record {i}, field '{field}' cannot be NaN"
                assert not math.isinf(value), \
                    f"Record {i}, field '{field}' cannot be Inf"


def test_correlation_values_range():
    """Test that correlation values are within the valid range [-1, 1]."""
    with open(OUTPUT_PATH, 'r') as f:
        results = json.load(f)

    if len(results) == 0:
        pytest.skip("No correlation records to validate (empty result set)")

    for i, record in enumerate(results):
        corr = record.get("correlation")
        assert -1.0 <= corr <= 1.0, \
            f"Record {i}: correlation {corr} is outside valid range [-1, 1]"


def test_p_value_range():
    """Test that p-values are within the valid range [0, 1]."""
    with open(OUTPUT_PATH, 'r') as f:
        results = json.load(f)

    if len(results) == 0:
        pytest.skip("No correlation records to validate (empty result set)")

    for i, record in enumerate(results):
        p_val = record.get("p_value")
        assert 0.0 <= p_val <= 1.0, \
            f"Record {i}: p_value {p_val} is outside valid range [0, 1]"


def test_q_value_range():
    """Test that q-values (FDR-adjusted) are within the valid range [0, 1]."""
    with open(OUTPUT_PATH, 'r') as f:
        results = json.load(f)

    if len(results) == 0:
        pytest.skip("No correlation records to validate (empty result set)")

    for i, record in enumerate(results):
        q_val = record.get("q_value")
        assert 0.0 <= q_val <= 1.0, \
            f"Record {i}: q_value {q_val} is outside valid range [0, 1]"


def test_significant_field_consistency():
    """Test that the 'significant' field is consistent with q_value <= 0.05."""
    with open(OUTPUT_PATH, 'r') as f:
        results = json.load(f)

    if len(results) == 0:
        pytest.skip("No correlation records to validate (empty result set)")

    for i, record in enumerate(results):
        q_val = record.get("q_value")
        is_significant = record.get("significant")

        expected_significant = q_val <= 0.05
        assert is_significant == expected_significant, \
            f"Record {i}: 'significant' ({is_significant}) inconsistent with q_value ({q_val})"