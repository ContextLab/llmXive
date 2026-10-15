import pytest
import pandas as pd
import os
from pathlib import Path
from llmxive_toolkit import paths
from code.retrieve_bulk_properties import validate_bulk_data

def test_validate_bulk_data_success():
    """Test that valid data passes validation."""
    data = {
        "pair_id": ["A", "B"],
        "density": [1.2, 1.3],
        "viscosity": [40.0, 50.0]
    }
    df = pd.DataFrame(data)
    validated_df = validate_bulk_data(df)
    assert len(validated_df) == 2
    assert list(validated_df.columns) == ["pair_id", "density", "viscosity"]

def test_validate_bulk_data_missing_col():
    """Test that missing columns raise ValueError."""
    data = {"pair_id": ["A"], "density": [1.2]} # missing viscosity
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match="missing required columns"):
        validate_bulk_data(df)

def test_validate_bulk_data_nan_handling():
    """Test that NaNs are dropped."""
    data = {
        "pair_id": ["A", "B", "C"],
        "density": [1.2, None, 1.4],
        "viscosity": [40.0, 50.0, None]
    }
    df = pd.DataFrame(data)
    validated_df = validate_bulk_data(df)
    # Only row A is complete
    assert len(validated_df) == 1
    assert validated_df.iloc[0]["pair_id"] == "A"

def test_output_file_exists():
    """Verify the processed file was actually created by the script."""
    processed_file = paths.data("processed", "bulk_properties.csv")
    assert processed_file.exists()
    df = pd.read_csv(processed_file)
    assert "pair_id" in df.columns
    assert "density" in df.columns
    assert "viscosity" in df.columns