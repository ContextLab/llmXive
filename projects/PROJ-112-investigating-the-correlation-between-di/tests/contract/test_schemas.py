"""
Contract tests for data schema validation.

These tests validate that the data produced by the ingestion pipeline
adheres to the expected schema definitions.
"""
import pytest
import pandas as pd
from typing import Dict, Any, List, Set
import os
from pathlib import Path

# Schema Definitions
# These define the required columns and basic type expectations for each stage.

HARMONIZED_SCHEMA = {
    "required_columns": {
        "sample_id",
        "cohort_id",
        "fiber_g_day",
        "read_count",
        # Taxon abundances and covariates are dynamic but must exist if generated
    },
    "mandatory_types": {
        "sample_id": str,
        "cohort_id": str,
        "fiber_g_day": (int, float),
        "read_count": (int, float),
    },
    "cohort_values": {"AGP", "UKBB"}
}

CLR_SCHEMA = {
    "required_columns": {
        "sample_id",
        "cohort_id",
        # CLR transformed taxa columns
    },
    "mandatory_types": {
        "sample_id": str,
        "cohort_id": str,
    },
    "forbidden_values": {float('nan'), float('inf'), float('-inf')}
}

ASSOCIATION_SCHEMA = {
    "required_columns": {
        "taxon",
        "maaslin2_beta",
        "maaslin2_se",
        "maaslin2_p_value",
        "maaslin2_q_value",
        "spearman_rho",
        "spearman_se",
        "spearman_p_value"
    },
    "mandatory_types": {
        "taxon": str,
        "maaslin2_beta": (int, float),
        "maaslin2_se": (int, float),
        "maaslin2_p_value": (int, float),
        "maaslin2_q_value": (int, float),
        "spearman_rho": (int, float),
        "spearman_se": (int, float),
        "spearman_p_value": (int, float)
    }
}

def validate_harmonized_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates a DataFrame against the Harmonized schema.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        Dict with 'valid' (bool) and 'errors' (list of str).
    """
    errors = []
    required_cols = HARMONIZED_SCHEMA["required_columns"]
    actual_cols = set(df.columns)
    
    missing_cols = required_cols - actual_cols
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    for col, expected_type in HARMONIZED_SCHEMA["mandatory_types"].items():
        if col in df.columns:
            if not df[col].apply(lambda x: isinstance(x, expected_type)).all():
                # Allow NaN for numeric types
                if not df[col].dropna().apply(lambda x: isinstance(x, expected_type)).all():
                    errors.append(f"Column '{col}' has invalid types. Expected {expected_type}")
        
    if "cohort_id" in df.columns:
        valid_values = HARMONIZED_SCHEMA["cohort_values"]
        invalid_values = set(df["cohort_id"].unique()) - valid_values
        if invalid_values:
            errors.append(f"Invalid cohort_id values found: {invalid_values}")
            
    return {"valid": len(errors) == 0, "errors": errors}

def validate_clr_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates a DataFrame against the CLR schema.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        Dict with 'valid' (bool) and 'errors' (list of str).
    """
    errors = []
    required_cols = CLR_SCHEMA["required_columns"]
    actual_cols = set(df.columns)
    
    missing_cols = required_cols - actual_cols
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        
    for col, expected_type in CLR_SCHEMA["mandatory_types"].items():
        if col in df.columns:
            if not df[col].apply(lambda x: isinstance(x, expected_type)).all():
                if not df[col].dropna().apply(lambda x: isinstance(x, expected_type)).all():
                    errors.append(f"Column '{col}' has invalid types. Expected {expected_type}")
    
    # Check for NaN/Inf
    forbidden = CLR_SCHEMA["forbidden_values"]
    numeric_cols = df.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        if df[col].isna().any():
            errors.append(f"Column '{col}' contains NaN values")
        if np.isinf(df[col]).any():
            errors.append(f"Column '{col}' contains Inf values")
            
    return {"valid": len(errors) == 0, "errors": errors}

def validate_association_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates a DataFrame against the Association Results schema.
    
    Args:
        df: DataFrame to validate.
        
    Returns:
        Dict with 'valid' (bool) and 'errors' (list of str).
    """
    errors = []
    required_cols = ASSOCIATION_SCHEMA["required_columns"]
    actual_cols = set(df.columns)
    
    missing_cols = required_cols - actual_cols
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        
    for col, expected_type in ASSOCIATION_SCHEMA["mandatory_types"].items():
        if col in df.columns:
            if not df[col].apply(lambda x: isinstance(x, expected_type)).all():
                if not df[col].dropna().apply(lambda x: isinstance(x, expected_type)).all():
                    errors.append(f"Column '{col}' has invalid types. Expected {expected_type}")
                    
    return {"valid": len(errors) == 0, "errors": errors}

class TestSchemas:
    """
    Test suite for schema validation logic.
    """
    
    def test_validate_harmonized_schema_valid(self):
        """Test that a valid harmonized dataframe passes validation."""
        data = {
            "sample_id": ["S1", "S2"],
            "cohort_id": ["AGP", "UKBB"],
            "fiber_g_day": [25.0, 40.0],
            "read_count": [10000, 15000]
        }
        df = pd.DataFrame(data)
        result = validate_harmonized_schema(df)
        assert result["valid"], f"Valid data failed: {result['errors']}"
        assert len(result["errors"]) == 0

    def test_validate_harmonized_schema_missing_column(self):
        """Test that a dataframe with missing columns fails."""
        data = {
            "sample_id": ["S1", "S2"],
            "fiber_g_day": [25.0, 40.0]
        }
        df = pd.DataFrame(data)
        result = validate_harmonized_schema(df)
        assert not result["valid"]
        assert "Missing required columns" in str(result["errors"])

    def test_validate_harmonized_schema_invalid_cohort(self):
        """Test that invalid cohort_id values are caught."""
        data = {
            "sample_id": ["S1", "S2"],
            "cohort_id": ["AGP", "INVALID"],
            "fiber_g_day": [25.0, 40.0],
            "read_count": [10000, 15000]
        }
        df = pd.DataFrame(data)
        result = validate_harmonized_schema(df)
        assert not result["valid"]
        assert "Invalid cohort_id values" in str(result["errors"])

    def test_validate_clr_schema_valid(self):
        """Test that a valid CLR dataframe passes validation."""
        import numpy as np
        data = {
            "sample_id": ["S1", "S2"],
            "cohort_id": ["AGP", "UKBB"],
            "taxon_A": [0.5, -0.2],
            "taxon_B": [1.1, 0.0]
        }
        df = pd.DataFrame(data)
        result = validate_clr_schema(df)
        assert result["valid"], f"Valid data failed: {result['errors']}"

    def test_validate_clr_schema_nan(self):
        """Test that CLR dataframe with NaN fails."""
        import numpy as np
        data = {
            "sample_id": ["S1", "S2"],
            "cohort_id": ["AGP", "UKBB"],
            "taxon_A": [0.5, np.nan],
            "taxon_B": [1.1, 0.0]
        }
        df = pd.DataFrame(data)
        result = validate_clr_schema(df)
        assert not result["valid"]
        assert "contains NaN values" in str(result["errors"])

    def test_validate_association_schema_valid(self):
        """Test that a valid association dataframe passes validation."""
        data = {
            "taxon": ["TaxonA", "TaxonB"],
            "maaslin2_beta": [0.5, -0.2],
            "maaslin2_se": [0.1, 0.1],
            "maaslin2_p_value": [0.01, 0.05],
            "maaslin2_q_value": [0.02, 0.06],
            "spearman_rho": [0.4, -0.3],
            "spearman_se": [0.1, 0.1],
            "spearman_p_value": [0.02, 0.04]
        }
        df = pd.DataFrame(data)
        result = validate_association_schema(df)
        assert result["valid"], f"Valid data failed: {result['errors']}"

    def test_validate_association_schema_missing_column(self):
        """Test that association dataframe with missing columns fails."""
        data = {
            "taxon": ["TaxonA"],
            "maaslin2_beta": [0.5]
        }
        df = pd.DataFrame(data)
        result = validate_association_schema(df)
        assert not result["valid"]
        assert "Missing required columns" in str(result["errors"])

# Import numpy for the test class methods if needed in future expansions
import numpy as np