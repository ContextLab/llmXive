"""
Contract test for environmental metadata schema (US1 - T011).

This test verifies that the environmental metadata schema validation
correctly rejects dataframes with missing required columns.

The schema expects the following columns to be present:
- sample_id: Unique identifier for the sample
- pH: Soil pH value
- nutrients: Nutrient availability metric
- biome: Biome classification
- temperature: Average temperature
- moisture: Soil moisture content

The test creates a synthetic dataframe with missing columns and asserts
that the validation function raises a ValueError.
"""

import pytest
import pandas as pd
from src.models.schemas import validate_environmental_metadata


REQUIRED_COLUMNS = [
    "sample_id",
    "pH",
    "nutrients",
    "biome",
    "temperature",
    "moisture"
]


def test_metadata_schema_missing_columns():
    """
    Verify that validation fails when required columns are missing.
    
    This test creates a dataframe with only 3 out of 6 required columns
    and expects validate_environmental_metadata to raise a ValueError.
    """
    # Create a dataframe with missing columns (only sample_id, pH, and temperature)
    incomplete_data = pd.DataFrame({
        "sample_id": ["S001", "S002", "S003"],
        "pH": [6.5, 7.2, 5.8],
        "temperature": [15.0, 18.5, 12.3]
        # Missing: nutrients, biome, moisture
    })
    
    with pytest.raises(ValueError) as exc_info:
        validate_environmental_metadata(incomplete_data)
    
    error_message = str(exc_info.value)
    assert "Missing required columns" in error_message
    
    # Verify that the error message lists the specific missing columns
    missing_cols = ["nutrients", "biome", "moisture"]
    for col in missing_cols:
        assert col in error_message, f"Error message should mention missing column: {col}"


def test_metadata_schema_empty_dataframe():
    """
    Verify that validation fails on an empty dataframe.
    
    An empty dataframe has no columns, so all required columns should be reported as missing.
    """
    empty_df = pd.DataFrame()
    
    with pytest.raises(ValueError) as exc_info:
        validate_environmental_metadata(empty_df)
    
    error_message = str(exc_info.value)
    assert "Missing required columns" in error_message
    
    # All required columns should be mentioned as missing
    for col in REQUIRED_COLUMNS:
        assert col in error_message, f"Error message should mention missing column: {col}"


def test_metadata_schema_extra_columns_allowed():
    """
    Verify that validation passes when dataframe has extra columns.
    
    The schema should only require specific columns but allow additional ones.
    """
    complete_data = pd.DataFrame({
        "sample_id": ["S001", "S002"],
        "pH": [6.5, 7.2],
        "nutrients": [100.0, 150.0],
        "biome": ["Forest", "Grassland"],
        "temperature": [15.0, 18.5],
        "moisture": [45.0, 60.0],
        "extra_column": ["A", "B"]  # Extra column should be allowed
    })
    
    # This should NOT raise an error
    try:
        result = validate_environmental_metadata(complete_data)
        # Verify the returned dataframe has the required columns
        for col in REQUIRED_COLUMNS:
            assert col in result.columns, f"Result should contain required column: {col}"
    except ValueError as e:
        pytest.fail(f"Validation should pass with extra columns, but failed: {e}")


def test_metadata_schema_valid_minimal():
    """
    Verify that validation passes with exactly the required columns.
    """
    valid_data = pd.DataFrame({
        "sample_id": ["S001", "S002", "S003"],
        "pH": [6.5, 7.2, 5.8],
        "nutrients": [100.0, 150.0, 120.0],
        "biome": ["Forest", "Grassland", "Desert"],
        "temperature": [15.0, 18.5, 22.0],
        "moisture": [45.0, 60.0, 25.0]
    })
    
    # This should NOT raise an error
    try:
        result = validate_environmental_metadata(valid_data)
        assert result is not None
        assert len(result) == 3
    except ValueError as e:
        pytest.fail(f"Validation should pass for complete data, but failed: {e}")