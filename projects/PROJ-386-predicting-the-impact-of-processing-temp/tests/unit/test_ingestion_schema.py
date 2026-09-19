import pytest
import pandas as pd
import os
import tempfile
from code.data.ingestion import check_schema_preconditions

def test_check_schema_preconditions_missing_columns():
    """
    Verify that check_schema_preconditions returns False for a mock CSV with missing columns.
    """
    # Create a temporary CSV with missing required columns
    mock_data = """
    id,other_column,value
    1,foo,100
    2,bar,200
    3,baz,300
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(mock_data)
        temp_path = f.name
    
    try:
        result = check_schema_preconditions(temp_path)
        assert result is False, "Expected False for CSV missing required columns"
    finally:
        os.unlink(temp_path)

def test_check_schema_preconditions_valid_columns():
    """
    Verify that check_schema_preconditions returns True for a mock CSV with required columns.
    """
    # Create a temporary CSV with required columns (using common aliases)
    mock_data = """
    id,rolling_temperature,alloy_composition,grain_size
    1,450.0,"Mg:1.5,Si:0.5",50.0
    2,500.0,"Mg:1.2,Si:0.6",55.0
    3,480.0,"Mg:1.8,Si:0.4",48.0
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(mock_data)
        temp_path = f.name
    
    try:
        result = check_schema_preconditions(temp_path)
        assert result is True, "Expected True for CSV with required columns"
    finally:
        os.unlink(temp_path)

def test_check_schema_preconditions_partial_columns():
    """
    Verify that check_schema_preconditions returns False if only some columns are present.
    """
    # Create a temporary CSV with only temperature
    mock_data = """
    id,rolling_temperature,value
    1,450.0,100
    2,500.0,200
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(mock_data)
        temp_path = f.name
    
    try:
        result = check_schema_preconditions(temp_path)
        assert result is False, "Expected False for CSV missing grain size and composition"
    finally:
        os.unlink(temp_path)
