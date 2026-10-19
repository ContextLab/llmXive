"""
Tests for the HEA data acquisition script.
"""
import pytest
import json
import pandas as pd
from pathlib import Path
from code.data.fetch_heas import _validate_row, _load_schema

def test_validate_row_missing_yield_strength():
    """
    Verify that a record missing 'yield_strength' raises ValueError (FR-009).
    """
    schema = _load_schema()
    # Row missing 'yield_strength'
    invalid_row = {
        "alloy_id": "TestAlloy",
        "composition": {"Al": 0.5, "Co": 0.5},
        # "yield_strength" is missing
    }
    
    with pytest.raises(ValueError, match="Row validation error"):
        _validate_row(invalid_row, schema)

def test_validate_row_valid():
    """
    Verify that a correct record passes validation.
    """
    schema = _load_schema()
    valid_row = {
        "alloy_id": "TestAlloy",
        "composition": {"Al": 0.5, "Co": 0.5},
        "yield_strength": 250.0
    }
    # Should not raise
    _validate_row(valid_row, schema)

def test_validate_row_invalid_composition():
    """
    Verify that invalid composition types raise ValueError.
    """
    schema = _load_schema()
    invalid_row = {
        "alloy_id": "TestAlloy",
        "composition": "not-a-dict",
        "yield_strength": 250.0
    }
    
    with pytest.raises(ValueError):
        _validate_row(invalid_row, schema)