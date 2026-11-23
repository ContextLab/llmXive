"""
Contract Test: Data Schema Validation for User Story 1
"""
import pandas as pd
import pytest
from pathlib import Path

def test_materials_master_schema():
    """Verify the schema of the consolidated materials dataset."""
    # This test expects the file to exist after T013
    file_path = Path("data/processed/materials_master.parquet")
    assert file_path.exists(), "materials_master.parquet not found. Run T013 first."

    df = pd.read_parquet(file_path)

    # Required columns
    required_columns = {"material_id", "property_name", "target_value"}
    assert required_columns.issubset(df.columns), f"Missing columns: {required_columns - set(df.columns)}"

    # Verify data types
    assert df["material_id"].dtype == "object", "material_id must be string/object"
    assert df["property_name"].dtype == "object", "property_name must be string/object"
    assert pd.api.types.is_numeric_dtype(df["target_value"]), "target_value must be numeric"

def test_scaling_results_schema():
    """Verify the schema of the scaling results dataset."""
    file_path = Path("data/processed/scaling_results.csv")
    if not file_path.exists():
        pytest.skip("scaling_results.csv not found. Run T020/T021 first.")

    df = pd.read_csv(file_path)

    required_columns = {"property_name", "exponent_b", "intercept_a", "r_squared", "fit_status"}
    assert required_columns.issubset(df.columns), f"Missing columns: {required_columns - set(df.columns)}"

    assert df["fit_status"].isin(["Power-Law", "Non-Power-Law"]).all(), "fit_status must be valid"
