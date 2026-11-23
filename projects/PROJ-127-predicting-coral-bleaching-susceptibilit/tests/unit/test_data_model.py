"""
Unit tests for data model generation.

Verifies that the data-model.md file is generated correctly and contains
the expected schema information.
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from generate_data_model import generate_schema_description, infer_dtype

def test_infer_dtype_integer():
    """Test integer dtype inference."""
    series = pd.Series([1, 2, 3])
    assert infer_dtype(series.dtype) == "integer"

def test_infer_dtype_float():
    """Test float dtype inference."""
    series = pd.Series([1.0, 2.0, 3.0])
    assert infer_dtype(series.dtype) == "float"

def test_infer_dtype_string():
    """Test string dtype inference."""
    series = pd.Series(["a", "b", "c"])
    assert infer_dtype(series.dtype) == "string"

def test_generate_schema_description():
    """Test schema description generation."""
    # Create a small test dataframe
    df = pd.DataFrame({
        'reef_id': [1, 2, 3],
        'sst_mean': [28.5, 29.1, 27.8],
        'dhw_mean': [3.2, 4.1, 2.5],
        'thermal_tolerance': [30.2, 31.0, 29.5],
        'bleaching_label': [1, 0, 1]
    })
    
    feature_names = ['sst_mean', 'dhw_mean', 'thermal_tolerance']
    schema_md = generate_schema_description(df, feature_names)
    
    # Verify key sections exist
    assert "# Data Model: Reef-Species Unified Dataset" in schema_md
    assert "## Overview" in schema_md
    assert "## Column Definitions" in schema_md
    assert "reef_id" in schema_md
    assert "sst_mean" in schema_md
    assert "bleaching_label" in schema_md
    assert "| Column Name | Type | Description | Source | Missing? |" in schema_md

def test_schema_contains_required_sections():
    """Test that the generated schema contains all required sections."""
    df = pd.DataFrame({
        'reef_id': [1],
        'lat': [10.0],
        'lon': [120.0],
        'sst_mean': [28.5],
        'dhw_mean': [3.2],
        'thermal_tolerance': [30.2],
        'bleaching_label': [1]
    })
    
    feature_names = ['sst_mean', 'dhw_mean', 'thermal_tolerance']
    schema_md = generate_schema_description(df, feature_names)
    
    required_sections = [
        "## Overview",
        "## Dataset Statistics",
        "## Column Definitions",
        "## Data Quality Notes",
        "## Usage",
        "## Version Information"
    ]
    
    for section in required_sections:
        assert section in schema_md, f"Missing required section: {section}"

def test_schema_correctly_identifies_sources():
    """Test that column sources are correctly identified."""
    df = pd.DataFrame({
        'reef_id': [1],
        'lat': [10.0],
        'lon': [120.0],
        'sst_mean': [28.5],
        'dhw_mean': [3.2],
        'trait_growth_rate': [1.5],
        'bleaching_label': [1]
    })
    
    feature_names = ['sst_mean', 'dhw_mean', 'trait_growth_rate']
    schema_md = generate_schema_description(df, feature_names)
    
    assert "NOAA" in schema_md
    assert "UNEP" in schema_md
    assert "Coral Trait DB" in schema_md
    assert "ReefBase" in schema_md