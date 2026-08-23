import pytest
from unittest.mock import patch, MagicMock
import logging
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from validate_sources import (
    validate_metadata,
    ERA5_PRODUCT_TYPE,
    ERA5_VARIABLE,
    ERA5_GRID_RESOLUTION,
    ERA5_PRODUCT_NAME,
    EXPECTED_PRODUCT_TYPE,
    EXPECTED_VARIABLE,
    EXPECTED_GRID_RESOLUTION,
    EXPECTED_PRODUCT_NAME
)

def test_validate_metadata_pass():
    """Test that validate_metadata returns 'Pass' when metadata matches expectations."""
    metadata = {
        'product_type': EXPECTED_PRODUCT_TYPE,
        'variable': EXPECTED_VARIABLE,
        'product_name': EXPECTED_PRODUCT_NAME,
        'grid_resolution': EXPECTED_GRID_RESOLUTION
    }
    score, details = validate_metadata(metadata)
    assert score == "Pass"
    assert len(details) == 4
    assert all("Match" in d for d in details)

def test_validate_metadata_fail_product_type():
    """Test that validate_metadata returns 'Fail' when product_type mismatches."""
    metadata = {
        'product_type': "wrong_type",
        'variable': EXPECTED_VARIABLE,
        'product_name': EXPECTED_PRODUCT_NAME,
        'grid_resolution': EXPECTED_GRID_RESOLUTION
    }
    score, details = validate_metadata(metadata)
    assert score == "Fail"
    assert any("Mismatch" in d and "product_type" in d for d in details)

def test_validate_metadata_fail_multiple():
    """Test that validate_metadata returns 'Fail' with multiple mismatches."""
    metadata = {
        'product_type': "wrong_type",
        'variable': "wrong_variable",
        'product_name': EXPECTED_PRODUCT_NAME,
        'grid_resolution': EXPECTED_GRID_RESOLUTION
    }
    score, details = validate_metadata(metadata)
    assert score == "Fail"
    assert sum(1 for d in details if "Mismatch" in d) == 2

def test_validate_metadata_missing_key():
    """Test that validate_metadata handles missing keys gracefully (treats as mismatch)."""
    metadata = {
        'product_type': EXPECTED_PRODUCT_TYPE,
        # Missing 'variable'
        'product_name': EXPECTED_PRODUCT_NAME,
        'grid_resolution': EXPECTED_GRID_RESOLUTION
    }
    score, details = validate_metadata(metadata)
    assert score == "Fail"
    assert any("Mismatch" in d and "variable" in d for d in details)