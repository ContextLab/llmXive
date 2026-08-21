"""
Unit tests for data validation module.
"""
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from analysis.validate_data import validate_numeric_types, validate_missing_values, run_validation


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "density": [2.5, 3.0, 4.2, 5.1, 6.8],
        "mass_fraction_Zr": [0.5, 0.4, 0.6, 0.3, 0.7],
        "mass_fraction_Cu": [0.3, 0.4, 0.2, 0.5, 0.2],
        "mass_fraction_Ni": [0.2, 0.2, 0.2, 0.2, 0.1],
        "composition": ["Zr50Cu30Ni20", "Zr40Cu40Ni20", "Zr60Cu20Ni20", "Zr30Cu50Ni20", "Zr70Cu20Ni10"]
    })


@pytest.fixture
def sample_dataframe_with_missing():
    """Create a sample DataFrame with missing target values."""
    return pd.DataFrame({
        "density": [2.5, np.nan, 4.2, np.nan, 6.8],
        "mass_fraction_Zr": [0.5, 0.4, 0.6, 0.3, 0.7],
        "mass_fraction_Cu": [0.3, 0.4, 0.2, 0.5, 0.2],
        "mass_fraction_Ni": [0.2, 0.2, 0.2, 0.2, 0.1],
        "composition": ["Zr50Cu30Ni20", "Zr40Cu40Ni20", "Zr60Cu20Ni20", "Zr30Cu50Ni20", "Zr70Cu20Ni10"]
    })


@pytest.fixture
def sample_dataframe_with_non_numeric():
    """Create a sample DataFrame with non-numeric mass fractions."""
    return pd.DataFrame({
        "density": [2.5, 3.0, 4.2, 5.1, 6.8],
        "mass_fraction_Zr": [0.5, 0.4, 0.6, 0.3, 0.7],
        "mass_fraction_Cu": ["0.3", 0.4, 0.2, 0.5, 0.2],  # String instead of float
        "mass_fraction_Ni": [0.2, 0.2, 0.2, 0.2, 0.1],
        "composition": ["Zr50Cu30Ni20", "Zr40Cu40Ni20", "Zr60Cu20Ni20", "Zr30Cu50Ni20", "Zr70Cu20Ni10"]
    })


def test_validate_numeric_types_valid(sample_dataframe):
    """Test validation with valid numeric types."""
    mass_cols = ["mass_fraction_Zr", "mass_fraction_Cu", "mass_fraction_Ni"]
    result = validate_numeric_types(sample_dataframe, mass_cols)
    
    assert result["valid"] is True
    assert len(result["invalid_columns"]) == 0
    assert all(result["details"][col] == "Valid numeric type" for col in mass_cols)


def test_validate_numeric_types_missing_column(sample_dataframe):
    """Test validation when a column is missing."""
    mass_cols = ["mass_fraction_Zr", "mass_fraction_Cu", "mass_fraction_Missing"]
    result = validate_numeric_types(sample_dataframe, mass_cols)
    
    assert result["valid"] is False
    assert "mass_fraction_Missing" in result["invalid_columns"]
    assert result["details"]["mass_fraction_Missing"] == "Column missing"


def test_validate_numeric_types_non_numeric(sample_dataframe_with_non_numeric):
    """Test validation with non-numeric types."""
    mass_cols = ["mass_fraction_Zr", "mass_fraction_Cu", "mass_fraction_Ni"]
    result = validate_numeric_types(sample_dataframe_with_non_numeric, mass_cols)
    
    assert result["valid"] is False
    assert "mass_fraction_Cu" in result["invalid_columns"]


def test_validate_missing_values_valid(sample_dataframe):
    """Test missing value validation with no missing values."""
    result = validate_missing_values(sample_dataframe, "density")
    
    assert result["valid"] is True
    assert result["missing_count"] == 0
    assert result["missing_percentage"] == 0.0


def test_validate_missing_values_with_missing(sample_dataframe_with_missing):
    """Test missing value validation with missing values."""
    result = validate_missing_values(sample_dataframe_with_missing, "density")
    
    assert result["valid"] is False
    assert result["missing_count"] == 2
    assert result["missing_percentage"] == 40.0


def test_validate_missing_values_missing_column(sample_dataframe):
    """Test missing value validation when target column is missing."""
    result = validate_missing_values(sample_dataframe, "nonexistent_column")
    
    assert result["valid"] is False
    assert result["missing_count"] == -1
    assert result["missing_percentage"] == -1.0


def test_run_validation_creates_log(sample_dataframe, tmp_path):
    """Test that run_validation creates the validation log file."""
    # Create a clean_data.csv
    clean_data_path = tmp_path / "clean_data.csv"
    sample_dataframe.to_csv(clean_data_path, index=False)
    
    # Run validation
    results = run_validation(tmp_path)
    
    # Check that validation_log.json was created
    log_path = tmp_path / "validation_log.json"
    assert log_path.exists()
    
    # Check log contents
    with open(log_path, "r") as f:
        log_data = json.load(f)
    
    assert log_data["source_file"] == "data/clean_data.csv"
    assert log_data["row_count"] == 5
    assert log_data["overall_valid"] is True
    assert log_data["missing_values"]["valid"] is True
    assert log_data["numeric_types"]["valid"] is True


def test_run_validation_with_missing_data(sample_dataframe_with_missing, tmp_path):
    """Test run_validation with data containing missing values."""
    clean_data_path = tmp_path / "clean_data.csv"
    sample_dataframe_with_missing.to_csv(clean_data_path, index=False)
    
    results = run_validation(tmp_path)
    
    log_path = tmp_path / "validation_log.json"
    assert log_path.exists()
    
    with open(log_path, "r") as f:
        log_data = json.load(f)
    
    assert log_data["overall_valid"] is False
    assert log_data["missing_values"]["valid"] is False
    assert log_data["missing_values"]["missing_count"] == 2
