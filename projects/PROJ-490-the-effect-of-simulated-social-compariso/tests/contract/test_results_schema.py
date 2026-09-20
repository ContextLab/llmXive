import json
import os
from pathlib import Path
import pytest
import pandas as pd
from utils.validators import validate_json_against_schema, load_schema

def test_regression_coefficients_csv_schema():
    """
    Contract test to verify regression_coefficients.csv matches the expected schema.
    This test ensures the CSV file contains the required columns and data types.
    """
    # Construct the expected path
    project_root = Path(__file__).parent.parent.parent
    output_file = project_root / "data" / "processed" / "regression_coefficients.csv"
    
    # Skip if file doesn't exist (task not yet run)
    if not output_file.exists():
        pytest.skip(f"File {output_file} does not exist yet. Run the pipeline first.")
    
    # Load the CSV
    df = pd.read_csv(output_file)
    
    # Define expected columns
    expected_columns = {'name', 'estimate', 'std_err', 'p_value', 'conf_int_low', 'conf_int_high'}
    
    # Check that all expected columns exist
    assert expected_columns.issubset(set(df.columns)), f"Missing columns: {expected_columns - set(df.columns)}"
    
    # Check data types
    assert df['estimate'].dtype in ['float64', 'int64'], "estimate column must be numeric"
    assert df['std_err'].dtype in ['float64', 'int64'], "std_err column must be numeric"
    assert df['p_value'].dtype in ['float64', 'int64'], "p_value column must be numeric"
    
    # Check that p_values are between 0 and 1
    assert (df['p_value'] >= 0).all() and (df['p_value'] <= 1).all(), "p_values must be between 0 and 1"

def test_model_diagnostics_json_schema():
    """
    Contract test to verify model_diagnostics.json matches the expected schema.
    This test validates the JSON structure against the results.schema.yaml.
    """
    # Construct the expected path
    project_root = Path(__file__).parent.parent.parent
    output_file = project_root / "data" / "processed" / "model_diagnostics.json"
    
    # Skip if file doesn't exist (task not yet run)
    if not output_file.exists():
        pytest.skip(f"File {output_file} does not exist yet. Run the pipeline first.")
    
    # Load the schema
    schema_path = project_root / "contracts" / "results.schema.yaml"
    if not schema_path.exists():
        pytest.skip(f"Schema file {schema_path} does not exist.")
    
    schema = load_schema(schema_path)
    
    # Load the JSON
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    # Validate against schema
    errors = validate_json_against_schema(data, schema)
    
    assert len(errors) == 0, f"Schema validation failed: {errors}"
    
    # Additional specific checks
    assert 'coefficients' in data, "Missing 'coefficients' key in diagnostics"
    assert 'assumptions' in data, "Missing 'assumptions' key in diagnostics"
    assert 'data_source_type' in data, "Missing 'data_source_type' key in diagnostics"
    
    # Check data_source_type is valid
    valid_types = ["real", "synthetic"]
    assert data['data_source_type'] in valid_types, f"Invalid data_source_type: {data['data_source_type']}"
    
    # Check assumptions structure
    assumptions = data['assumptions']
    assert 'shapiro_p' in assumptions, "Missing 'shapiro_p' in assumptions"
    assert 'breusch_pagan_p' in assumptions, "Missing 'breusch_pagan_p' in assumptions"
    assert 'vif_max' in assumptions, "Missing 'vif_max' in assumptions"