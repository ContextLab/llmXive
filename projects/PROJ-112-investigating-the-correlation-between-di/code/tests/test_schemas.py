"""
Contract tests for data schemas in the llmXive research pipeline.
Validates that data files conform to expected schemas.
"""
import pytest
import pandas as pd
from typing import Dict, Any

# Expected schemas for various data files
SCHEMAS = {
    "harmonized": {
        "required_columns": [
            "sample_id", "cohort_id", "fiber_g_day", "read_count",
            "taxon_abundances", "covariates"
        ],
        "optional_columns": []
    },
    "clr_transformed": {
        "required_columns": ["sample_id", "taxon", "clr_abundance"],
        "optional_columns": []
    },
    "association_results": {
        "required_columns": [
            "taxon", "maaslin2_beta", "maaslin2_se", "maaslin2_p_value",
            "maaslin2_q_value", "spearman_rho", "spearman_se", "spearman_p_value"
        ],
        "optional_columns": []
    }
}

def validate_harmonized_schema(df: pd.DataFrame) -> bool:
    """
    Validate that a DataFrame matches the harmonized dataset schema.
    
    Args:
        df: DataFrame to validate.
    
    Returns:
        True if schema is valid, False otherwise.
    """
    required = SCHEMAS["harmonized"]["required_columns"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in harmonized data: {missing}")
    return True

def validate_clr_schema(df: pd.DataFrame) -> bool:
    """
    Validate that a DataFrame matches the CLR transformed schema.
    
    Args:
        df: DataFrame to validate.
    
    Returns:
        True if schema is valid, False otherwise.
    """
    required = SCHEMAS["clr_transformed"]["required_columns"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in CLR data: {missing}")
    return True

class TestSchemas:
    """Test suite for schema validation."""
    
    def test_harmonized_schema_valid(self):
        """Test that a valid harmonized DataFrame passes validation."""
        data = {
            "sample_id": ["S1", "S2"],
            "cohort_id": ["AGP", "UKBB"],
            "fiber_g_day": [25.0, 30.0],
            "read_count": [10000, 15000],
            "taxon_abundances": [0.1, 0.2],
            "covariates": [0.5, 0.6]
        }
        df = pd.DataFrame(data)
        assert validate_harmonized_schema(df) is True

    def test_harmonized_schema_missing_columns(self):
        """Test that a harmonized DataFrame with missing columns fails validation."""
        data = {
            "sample_id": ["S1", "S2"],
            "fiber_g_day": [25.0, 30.0]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            validate_harmonized_schema(df)

    def test_clr_schema_valid(self):
        """Test that a valid CLR DataFrame passes validation."""
        data = {
            "sample_id": ["S1", "S2"],
            "taxon": ["TaxonA", "TaxonB"],
            "clr_abundance": [0.1, -0.2]
        }
        df = pd.DataFrame(data)
        assert validate_clr_schema(df) is True

    def test_clr_schema_missing_columns(self):
        """Test that a CLR DataFrame with missing columns fails validation."""
        data = {
            "sample_id": ["S1", "S2"],
            "taxon": ["TaxonA", "TaxonB"]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            validate_clr_schema(df)
