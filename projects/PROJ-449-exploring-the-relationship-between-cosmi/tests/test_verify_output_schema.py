"""
Unit tests for the output schema verification logic (T038).
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
from code.verify_output_schema import verify_schema

def create_temp_csv(columns, data, filename="test.csv"):
    """Helper to create a temporary CSV file with given columns and data."""
    df = pd.DataFrame(data, columns=columns)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', dir=tempfile.gettempdir()) as f:
        path = f.name
        df.to_csv(f, index=False)
    return Path(path)

def test_valid_schema():
    """Test that a valid schema passes verification."""
    data = {
        'date': pd.date_range('2020-01-01', periods=5),
        'rigidity_bin': [1.0, 2.0, 5.0, 10.0, 20.0],
        'proton_flux': [100.0, 90.0, 80.0, 70.0, 60.0],
        'helium_flux': [10.0, 9.0, 8.0, 7.0, 6.0],
        'heavy_flux': [1.0, 0.9, 0.8, 0.7, 0.6],
        'sunspot_number': [10, 12, 15, 14, 13]
    }
    path = create_temp_csv(list(data.keys()), data)
    
    try:
        assert verify_schema(path) is True
    finally:
        os.unlink(path)

def test_missing_column():
    """Test that a missing column fails verification."""
    data = {
        'date': pd.date_range('2020-01-01', periods=5),
        'rigidity_bin': [1.0, 2.0, 5.0, 10.0, 20.0],
        'proton_flux': [100.0, 90.0, 80.0, 70.0, 60.0],
        'helium_flux': [10.0, 9.0, 8.0, 7.0, 6.0],
        'heavy_flux': [1.0, 0.9, 0.8, 0.7, 0.6]
        # Missing 'sunspot_number'
    }
    path = create_temp_csv(list(data.keys()), data)
    
    try:
        assert verify_schema(path) is False
    finally:
        os.unlink(path)

def test_wrong_dtype():
    """Test that wrong data types fail verification."""
    data = {
        'date': ['2020-01-01'] * 5, # String instead of datetime
        'rigidity_bin': [1.0, 2.0, 5.0, 10.0, 20.0],
        'proton_flux': [100.0, 90.0, 80.0, 70.0, 60.0],
        'helium_flux': [10.0, 9.0, 8.0, 7.0, 6.0],
        'heavy_flux': [1.0, 0.9, 0.8, 0.7, 0.6],
        'sunspot_number': ['10', '12', '15', '14', '13'] # String instead of int
    }
    path = create_temp_csv(list(data.keys()), data)
    
    try:
        # Note: The verify_schema function attempts to convert date, but not sunspot_number
        # So this should fail due to sunspot_number type
        assert verify_schema(path) is False
    finally:
        os.unlink(path)

def test_file_not_found():
    """Test that a non-existent file fails verification."""
    path = Path("/tmp/non_existent_file.csv")
    assert verify_schema(path) is False