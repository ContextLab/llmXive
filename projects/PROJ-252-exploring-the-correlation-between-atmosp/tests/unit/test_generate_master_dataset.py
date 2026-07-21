"""
Unit tests for T017: Generate master dataset.
"""
import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
import json
import yaml

# Mock config for testing
class MockConfig:
    @staticmethod
    def get_processed_path(filename):
        return os.path.join(tempfile.gettempdir(), filename)
    
    @staticmethod
    def get_deviations_path():
        return "docs/deviations.md"

def test_assign_control_labels():
    """Test that control labels are correctly assigned."""
    from generate_master_dataset import assign_control_labels
    
    df = pd.DataFrame({
        'event_id': ['EQ001', 'EQ002'],
        'pressure_value': [1013.25, 1012.50],
        'anomaly_value': [-0.5, 0.2],
        'timestamp': ['2018-01-01', '2018-01-02']
    })
    
    result = assign_control_labels(df)
    
    assert 'window_label' in result.columns
    assert all(result['window_label'] == 'event')
    assert len(result) == 2

def test_validate_row_against_schema():
    """Test schema validation logic."""
    from generate_master_dataset import validate_row_against_schema
    
    schema = {
        'properties': {
            'magnitude': {'type': 'number'},
            'event_id': {'type': 'string'}
        },
        'required': ['magnitude', 'event_id']
    }
    
    # Valid row
    valid_row = {'magnitude': 5.0, 'event_id': 'EQ001'}
    errors = validate_row_against_schema(valid_row, schema, "test_schema")
    assert len(errors) == 0
    
    # Invalid row (missing required)
    invalid_row = {'magnitude': 5.0}
    errors = validate_row_against_schema(invalid_row, schema, "test_schema")
    assert len(errors) > 0
    assert "Missing required field 'event_id'" in errors[0]
    
    # Invalid type
    type_error_row = {'magnitude': 'high', 'event_id': 'EQ001'}
    errors = validate_row_against_schema(type_error_row, schema, "test_schema")
    assert len(errors) > 0
    assert "should be number" in errors[0]

def test_generate_checksum():
    """Test checksum generation."""
    from generate_master_dataset import generate_checksum
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test data")
        temp_path = f.name
    
    try:
        checksum = generate_checksum(temp_path)
        assert len(checksum) == 64  # SHA256 hex length
    finally:
        os.unlink(temp_path)

def test_get_expected_count():
    """Test expected count retrieval."""
    from generate_master_dataset import get_expected_count
    
    # This should return 12 by default for the pilot
    count = get_expected_count()
    assert isinstance(count, int)
    assert count > 0
