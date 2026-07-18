"""
Contract test for ASV table schema validation.

Verifies that the ASV table schema validation logic correctly fails
on invalid schemas (missing required columns, wrong data types).

This test implements TDD: it should fail before the implementation
is complete and pass after.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.pipelines.ingest import validate_metadata_columns
from src.config.constants import get_config

# Define expected ASV table schema based on data-model.md
ASV_REQUIRED_COLUMNS = ["sample_id", "asv_id", "count"]

def create_valid_asv_table():
    """Create a valid ASV table with correct schema."""
    data = {
        "sample_id": ["sample_001", "sample_001", "sample_002"],
        "asv_id": ["asv_001", "asv_002", "asv_001"],
        "count": [100, 50, 200]
    }
    return pd.DataFrame(data)

def create_invalid_asv_table_missing_columns():
    """Create an ASV table missing required columns."""
    data = {
        "sample_id": ["sample_001", "sample_001"],
        "asv_id": ["asv_001", "asv_002"]
        # Missing 'count' column
    }
    return pd.DataFrame(data)

def create_invalid_asv_table_wrong_types():
    """Create an ASV table with wrong data types."""
    data = {
        "sample_id": ["sample_001", "sample_001"],
        "asv_id": ["asv_001", "asv_002"],
        "count": ["not_a_number", "also_not_a_number"]  # Should be numeric
    }
    return pd.DataFrame(data)

def create_invalid_asv_table_empty():
    """Create an empty ASV table."""
    return pd.DataFrame(columns=ASV_REQUIRED_COLUMNS)

def test_asv_schema_valid_table():
    """Test that a valid ASV table passes validation."""
    df = create_valid_asv_table()
    # This should not raise an exception
    result = validate_metadata_columns(df, ASV_REQUIRED_COLUMNS)
    assert result is True

def test_asv_schema_missing_columns_fails():
    """Test that an ASV table with missing columns fails validation."""
    df = create_invalid_asv_table_missing_columns()
    with pytest.raises(ValueError) as exc_info:
        validate_metadata_columns(df, ASV_REQUIRED_COLUMNS)
    
    # Verify the error message mentions missing columns
    error_msg = str(exc_info.value).lower()
    assert "missing" in error_msg or "count" in error_msg

def test_asv_schema_wrong_types_fails():
    """Test that an ASV table with wrong data types fails validation."""
    df = create_invalid_asv_table_wrong_types()
    with pytest.raises(ValueError) as exc_info:
        validate_metadata_columns(df, ASV_REQUIRED_COLUMNS)
    
    # Verify the error message mentions type issues
    error_msg = str(exc_info.value).lower()
    assert "type" in error_msg or "numeric" in error_msg or "count" in error_msg

def test_asv_schema_empty_table_fails():
    """Test that an empty ASV table fails validation (min_samples constraint)."""
    df = create_invalid_asv_table_empty()
    # Empty tables should fail due to min_samples constraint (default 10)
    with pytest.raises(ValueError) as exc_info:
        validate_metadata_columns(df, ASV_REQUIRED_COLUMNS)
    
    error_msg = str(exc_info.value).lower()
    assert "empty" in error_msg or "sample" in error_msg

def test_asv_schema_extra_columns_allowed():
    """Test that ASV tables with extra columns are still valid."""
    df = create_valid_asv_table()
    df["extra_column"] = [1, 2, 3]  # Extra column should be allowed
    
    # Should not raise an exception
    result = validate_metadata_columns(df, ASV_REQUIRED_COLUMNS)
    assert result is True

def test_asv_schema_case_sensitivity():
    """Test that column names are case-sensitive."""
    df = create_valid_asv_table()
    # Rename columns to lowercase
    df.columns = ["sample_id", "asv_id", "count"]
    
    # Should still pass
    result = validate_metadata_columns(df, ASV_REQUIRED_COLUMNS)
    assert result is True