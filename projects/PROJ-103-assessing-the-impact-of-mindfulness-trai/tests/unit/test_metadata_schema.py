"""
Unit tests for the dataset metadata schema enforcement.
"""

import pytest
from src.datasets.metadata_schema import (
    validate_schema, 
    create_sample_metadata, 
    InterventionType, 
    ScanType
)

def test_valid_sample():
    """Ensure that the provided sample metadata is valid."""
    sample = create_sample_metadata()
    assert validate_schema(sample) is True

def test_missing_required_field():
    """Ensure that missing required fields cause validation failure."""
    sample = create_sample_metadata()
    del sample["dataset_id"]
    assert validate_schema(sample) is False

def test_invalid_type():
    """Ensure that incorrect data types cause validation failure."""
    sample = create_sample_metadata()
    sample["pre_scan_count"] = "twenty"  # Should be integer
    assert validate_schema(sample) is False

def test_invalid_enum_value():
    """Ensure that invalid enum values cause validation failure."""
    sample = create_sample_metadata()
    sample["intervention_type"] = "magic_pills"  # Not in InterventionType
    assert validate_schema(sample) is False

def test_invalid_coordinates_format():
    """Ensure that malformed coordinates cause validation failure."""
    sample = create_sample_metadata()
    # Missing 'z' coordinate
    sample["dmn_coordinates"]["PCC"] = {"x": 0.0, "y": -52.0}
    assert validate_schema(sample) is False

def test_negative_counts():
    """Ensure that negative scan counts are rejected."""
    sample = create_sample_metadata()
    sample["pre_scan_count"] = -1
    assert validate_schema(sample) is False