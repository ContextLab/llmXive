"""
Contract test for metadata schema.
Implements validate_metadata_schema function to ensure metadata.csv
conforms to the required schema defined in the project specifications.

Depends on T007 (base data models).
"""

import os
import sys
import pandas as pd
import pytest
from pathlib import Path

# Add parent directory to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_models import PlanetCategory

# Required columns as per T012 specification
REQUIRED_COLUMNS = [
    "planet_name",
    "temperature",
    "metallicity",
    "snr",
    "resolution",
    "planet_category",
    "instrument",
    "wavelength_range"
]

# Expected data types for validation
COLUMN_TYPES = {
    "planet_name": str,
    "temperature": (int, float),
    "metallicity": (int, float),
    "snr": (int, float),
    "resolution": (int, float),
    "planet_category": str,
    "instrument": str,
    "wavelength_range": str
}

# Valid categories based on T011c classification logic
VALID_CATEGORIES = {"Hot Jupiter", "Temperate Super-Earth"}

def validate_metadata_schema(df: pd.DataFrame) -> dict:
    """
    Validate that a DataFrame conforms to the metadata schema.
    
    Args:
        df: DataFrame to validate (expected from data/processed/metadata.csv)
    
    Returns:
        dict: Validation results with 'valid' boolean and 'errors' list
    """
    errors = []
    warnings = []
    
    # Check 1: Required columns exist
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
    
    # Check 2: Column data types
    for col, expected_type in COLUMN_TYPES.items():
        if col in df.columns:
            # Check for non-null values first
            if df[col].isnull().any():
                errors.append(f"Column '{col}' contains null values")
            
            # Type checking (allow numeric types to be int or float)
            if not df[col].apply(lambda x: isinstance(x, expected_type) if isinstance(expected_type, tuple) else isinstance(x, expected_type)).all():
                errors.append(f"Column '{col}' has incorrect data type. Expected {expected_type}")
    
    # Check 3: Planet category validity
    if "planet_category" in df.columns:
        invalid_categories = set(df["planet_category"].unique()) - VALID_CATEGORIES
        if invalid_categories:
            errors.append(f"Invalid planet categories found: {invalid_categories}")
    
    # Check 4: Numeric ranges (basic sanity checks)
    if "temperature" in df.columns:
        if (df["temperature"] <= 0).any():
            errors.append("Temperature values must be positive")
    
    if "snr" in df.columns:
        if (df["snr"] < 0).any():
            errors.append("SNR values cannot be negative")
    
    if "resolution" in df.columns:
        if (df["resolution"] <= 0).any():
            errors.append("Resolution values must be positive")
    
    # Check 5: Row count sanity (from T013b requirement)
    if len(df) == 0:
        warnings.append("Metadata file is empty (0 rows)")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(df),
        "column_count": len(df.columns)
    }

def test_validate_metadata_schema_valid_file():
    """Test validation against a valid metadata file if it exists."""
    metadata_path = Path(__file__).parent.parent.parent / "data" / "processed" / "metadata.csv"
    
    if not metadata_path.exists():
        pytest.skip(f"Test data not available: {metadata_path}")
    
    df = pd.read_csv(metadata_path)
    result = validate_metadata_schema(df)
    
    assert result["valid"] is True, f"Validation failed: {result['errors']}"
    assert result["row_count"] > 0, "Expected non-empty dataset"

def test_validate_metadata_schema_missing_columns():
    """Test validation fails when required columns are missing."""
    df = pd.DataFrame({
        "planet_name": ["test"],
        "temperature": [1000.0]
    })
    result = validate_metadata_schema(df)
    
    assert result["valid"] is False
    assert any("Missing required columns" in err for err in result["errors"])

def test_validate_metadata_schema_null_values():
    """Test validation fails when required columns have null values."""
    df = pd.DataFrame({
        "planet_name": [None],
        "temperature": [1000.0],
        "metallicity": [0.0],
        "snr": [10.0],
        "resolution": [50.0],
        "planet_category": ["Hot Jupiter"],
        "instrument": ["HST"],
        "wavelength_range": ["0.5-2.5"]
    })
    result = validate_metadata_schema(df)
    
    assert result["valid"] is False
    assert any("null values" in err for err in result["errors"])

def test_validate_metadata_schema_invalid_category():
    """Test validation fails when planet category is invalid."""
    df = pd.DataFrame({
        "planet_name": ["test"],
        "temperature": [1000.0],
        "metallicity": [0.0],
        "snr": [10.0],
        "resolution": [50.0],
        "planet_category": ["Invalid Category"],
        "instrument": ["HST"],
        "wavelength_range": ["0.5-2.5"]
    })
    result = validate_metadata_schema(df)
    
    assert result["valid"] is False
    assert any("Invalid planet categories" in err for err in result["errors"])

def test_validate_metadata_schema_negative_values():
    """Test validation fails for physically impossible negative values."""
    df = pd.DataFrame({
        "planet_name": ["test"],
        "temperature": [-100.0],
        "metallicity": [0.0],
        "snr": [10.0],
        "resolution": [50.0],
        "planet_category": ["Hot Jupiter"],
        "instrument": ["HST"],
        "wavelength_range": ["0.5-2.5"]
    })
    result = validate_metadata_schema(df)
    
    assert result["valid"] is False
    assert any("Temperature values must be positive" in err for err in result["errors"])

if __name__ == "__main__":
    # Run basic self-test
    print("Running contract test for metadata schema...")
    
    # Test 1: Valid schema structure
    test_df = pd.DataFrame({
        "planet_name": ["HD 209458 b"],
        "temperature": [1450.0],
        "metallicity": [0.0],
        "snr": [15.0],
        "resolution": [100.0],
        "planet_category": ["Hot Jupiter"],
        "instrument": ["HST"],
        "wavelength_range": ["0.6-1.7"]
    })
    
    result = validate_metadata_schema(test_df)
    assert result["valid"], f"Valid test failed: {result['errors']}"
    print("✓ Valid schema test passed")
    
    # Test 2: Missing columns
    invalid_df = pd.DataFrame({"planet_name": ["test"]})
    result = validate_metadata_schema(invalid_df)
    assert not result["valid"], "Missing columns test should fail"
    print("✓ Missing columns test passed")
    
    # Test 3: Invalid category
    invalid_df = pd.DataFrame({
        "planet_name": ["test"],
        "temperature": [1000.0],
        "metallicity": [0.0],
        "snr": [10.0],
        "resolution": [50.0],
        "planet_category": ["Unknown"],
        "instrument": ["HST"],
        "wavelength_range": ["0.5-2.5"]
    })
    result = validate_metadata_schema(invalid_df)
    assert not result["valid"], "Invalid category test should fail"
    print("✓ Invalid category test passed")
    
    print("All contract tests passed.")