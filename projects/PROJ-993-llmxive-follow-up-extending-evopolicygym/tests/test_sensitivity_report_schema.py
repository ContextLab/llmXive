"""
Tests for the sensitivity report schema definition and utilities.
"""
import pytest
import os
import tempfile
import csv
from code.analysis.sensitivity_report_schema import (
    SensitivityReportRow,
    validate_row,
    write_header_only,
    write_sensitivity_report,
    read_sensitivity_report,
    SCHEMA_COLUMNS
)

def test_schema_columns_defined():
    """Verify that the schema columns match the task requirements."""
    expected = ['env_id', 'shift_step', 'pre_shift_score', 'post_shift_score', 'drop_rate', 'p_value']
    assert SCHEMA_COLUMNS == expected

def test_validate_row_valid():
    """Test validation of a correctly formatted row."""
    row = {
        'env_id': 'env_001',
        'shift_step': 50,
        'pre_shift_score': 100.0,
        'post_shift_score': 80.0,
        'drop_rate': 0.2,
        'p_value': 0.01
    }
    assert validate_row(row) is True

def test_validate_row_invalid_drop_rate():
    """Test validation rejects drop_rate outside [0.0, 1.0]."""
    row = {
        'env_id': 'env_001',
        'shift_step': 50,
        'pre_shift_score': 100.0,
        'post_shift_score': 80.0,
        'drop_rate': 1.5,
        'p_value': 0.01
    }
    assert validate_row(row) is False

def test_validate_row_missing_field():
    """Test validation rejects row with missing field."""
    row = {
        'env_id': 'env_001',
        'shift_step': 50,
        'pre_shift_score': 100.0,
        'post_shift_score': 80.0,
        # missing drop_rate and p_value
    }
    assert validate_row(row) is False

def test_write_and_read_header_only():
    """Test writing header-only file and reading it back."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        path = f.name
    
    try:
        write_header_only(path)
        rows = read_sensitivity_report(path)
        assert rows == []
        
        # Verify header exists
        with open(path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == SCHEMA_COLUMNS
    finally:
        os.unlink(path)

def test_write_and_read_full_report():
    """Test writing a full report and reading it back."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        path = f.name
    
    try:
        rows_to_write = [
            {
                'env_id': 'env_A',
                'shift_step': 100,
                'pre_shift_score': 50.0,
                'post_shift_score': 20.0,
                'drop_rate': 0.6,
                'p_value': 0.001
            },
            {
                'env_id': 'env_B',
                'shift_step': 200,
                'pre_shift_score': 10.0,
                'post_shift_score': 5.0,
                'drop_rate': 0.5,
                'p_value': 0.04
            }
        ]
        
        write_sensitivity_report(path, rows_to_write)
        rows_read = read_sensitivity_report(path)
        
        assert len(rows_read) == 2
        assert rows_read[0]['env_id'] == 'env_A'
        assert rows_read[0]['shift_step'] == 100
        assert rows_read[0]['pre_shift_score'] == 50.0
        assert rows_read[0]['post_shift_score'] == 20.0
        assert rows_read[0]['drop_rate'] == 0.6
        assert rows_read[0]['p_value'] == 0.001
        
        assert rows_read[1]['env_id'] == 'env_B'
    finally:
        os.unlink(path)