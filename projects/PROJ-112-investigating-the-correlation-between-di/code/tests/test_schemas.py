"""
Schema validation tests for the project.
Ensures data outputs conform to expected structures.
"""
import pytest
import pandas as pd
from typing import Dict, Any

def validate_harmonized_schema(df: pd.DataFrame) -> bool:
    """
    Validates the schema of the harmonized dataset.
    
    Expected columns:
    - sample_id
    - fiber_g_day
    - read_count
    - cohort
    """
    required_columns = {"sample_id", "fiber_g_day", "read_count", "cohort"}
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        raise ValueError(f"Missing required columns in harmonized data: {missing}")
    return True

def validate_clr_schema(df: pd.DataFrame) -> bool:
    """
    Validates the schema of the CLR transformed dataset.
    
    Expected columns:
    - sample_id
    - Taxon columns (float)
    """
    if "sample_id" not in df.columns:
        raise ValueError("Missing sample_id column in CLR data")
    
    # Check that at least one non-ID column exists and is numeric
    non_id_cols = [c for c in df.columns if c != "sample_id"]
    if not non_id_cols:
        raise ValueError("No taxon columns found in CLR data")
    
    for col in non_id_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column {col} is not numeric in CLR data")
    
    return True

class TestSchemas:
    """Test cases for schema validation."""
    
    def test_harmonized_schema_valid(self):
        """Test validation of a valid harmonized dataframe."""
        data = {
            "sample_id": ["S1", "S2"],
            "fiber_g_day": [10.5, 25.0],
            "read_count": [10000, 5000],
            "cohort": ["AGP", "UKBB"]
        }
        df = pd.DataFrame(data)
        assert validate_harmonized_schema(df) is True

    def test_harmonized_schema_missing_column(self):
        """Test validation fails on missing column."""
        data = {
            "sample_id": ["S1"],
            "fiber_g_day": [10.5],
            "read_count": [10000]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            validate_harmonized_schema(df)

    def test_clr_schema_valid(self):
        """Test validation of a valid CLR dataframe."""
        data = {
            "sample_id": ["S1", "S2"],
            "Bacteroides": [0.1, 0.2],
            "Firmicutes": [0.3, 0.4]
        }
        df = pd.DataFrame(data)
        assert validate_clr_schema(df) is True

    def test_clr_schema_missing_id(self):
        """Test validation fails on missing sample_id."""
        data = {
            "Bacteroides": [0.1, 0.2],
            "Firmicutes": [0.3, 0.4]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            validate_clr_schema(df)
