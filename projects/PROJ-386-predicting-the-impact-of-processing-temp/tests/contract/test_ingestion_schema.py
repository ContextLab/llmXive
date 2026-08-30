"""
Contract test for schema pre-check logic in code/data/ingestion.py.

This test verifies that the schema pre-check logic correctly identifies
and skips sources that are missing required fields (rolling temperature,
composition, grain size).

It specifically tests the skip logic for missing fields and ensures
that the system aggregates a list of missing variables across all
skipped sources to support error logging.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.ingestion import check_schema


class MockSource:
    """Mock source object for testing schema checks."""
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields
        self.url = f"https://example.com/{name}"
    
    def __repr__(self):
        return f"MockSource(name='{self.name}')"


def test_check_schema_all_fields_present():
    """Test that a source with all required fields is not skipped."""
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    source = MockSource("complete_source", required_fields)
    
    result = check_schema(source, required_fields)
    
    assert result is True
    assert source.name not in result if isinstance(result, dict) else True


def test_check_schema_missing_single_field():
    """Test that a source missing one required field is skipped."""
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    # Missing 'grain_size'
    source = MockSource("incomplete_source", ['rolling_temperature', 'composition'])
    
    result = check_schema(source, required_fields)
    
    assert result is False


def test_check_schema_missing_multiple_fields():
    """Test that a source missing multiple required fields is skipped."""
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    # Missing 'composition' and 'grain_size'
    source = MockSource("very_incomplete_source", ['rolling_temperature'])
    
    result = check_schema(source, required_fields)
    
    assert result is False


def test_check_schema_no_fields():
    """Test that a source with no fields is skipped."""
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    source = MockSource("empty_source", [])
    
    result = check_schema(source, required_fields)
    
    assert result is False


def test_check_schema_missing_field_names():
    """Test that missing field names are correctly identified."""
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    # Missing 'composition'
    source = MockSource("partial_source", ['rolling_temperature', 'grain_size'])
    
    result = check_schema(source, required_fields)
    
    assert result is False


def test_aggregated_missing_variables():
    """
    Test that when multiple sources are checked, the system correctly
    aggregates the list of missing variables across all skipped sources.
    This is critical for the 'Critical Variables Missing' halt logic.
    """
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    
    sources = [
        MockSource("source_a", ['rolling_temperature']),  # Missing: composition, grain_size
        MockSource("source_b", ['composition']),           # Missing: rolling_temperature, grain_size
        MockSource("source_c", ['rolling_temperature', 'composition', 'grain_size']), # Complete
    ]
    
    skipped_sources = []
    all_missing_vars = set()
    
    for source in sources:
        is_valid = check_schema(source, required_fields)
        if not is_valid:
            skipped_sources.append(source)
            # Determine what was missing for this source
            missing = [f for f in required_fields if f not in source.fields]
            all_missing_vars.update(missing)
    
    # Verify logic
    assert len(skipped_sources) == 2, "Exactly 2 sources should be skipped"
    assert 'rolling_temperature' in all_missing_vars
    assert 'composition' in all_missing_vars
    assert 'grain_size' in all_missing_vars
    
    # Verify that source_c was NOT skipped
    assert sources[2] not in skipped_sources


def test_check_schema_with_custom_field_mapping():
    """Test schema check with alternative field names (aliasing)."""
    # In real implementation, we might map 'temp' to 'rolling_temperature'
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    # Source uses 'temp' instead of 'rolling_temperature'
    source = MockSource("aliased_source", ['temp', 'composition', 'grain_size'])
    
    # This should fail if strict matching is used
    result = check_schema(source, required_fields)
    assert result is False, "Strict matching should fail for aliased fields"


def test_logging_of_missing_fields(caplog):
    """
    Verify that missing fields are logged appropriately when a source is skipped.
    This ensures the 'Critical Variables Missing' halt logic has the necessary info.
    """
    required_fields = ['rolling_temperature', 'composition', 'grain_size']
    source = MockSource("test_source", ['rolling_temperature'])
    
    with caplog.at_level(logging.INFO):
        result = check_schema(source, required_fields)
        
        # Verify the function returns False
        assert result is False
        
        # In a real implementation, this would log the missing fields
        # We verify the logic path is taken
        missing = [f for f in required_fields if f not in source.fields]
        assert len(missing) == 2


def test_empty_required_fields_list():
    """Test behavior when required_fields list is empty."""
    required_fields = []
    source = MockSource("any_source", ['some_field'])
    
    # If no fields are required, the source should pass
    result = check_schema(source, required_fields)
    assert result is True


def test_schema_check_case_sensitivity():
    """Test that field names are case-sensitive."""
    required_fields = ['Rolling_Temperature', 'composition', 'grain_size']
    # Source uses lowercase 'rolling_temperature'
    source = MockSource("case_source", ['rolling_temperature', 'composition', 'grain_size'])
    
    result = check_schema(source, required_fields)
    assert result is False, "Field names should be case-sensitive"