import pytest
import pandas as pd
import yaml
import os

def load_schema_contract():
    """Loads the schema contract from the YAML file."""
    schema_path = os.path.join("contracts", "dataset.schema.yaml")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_schema_matches_yaml():
    """Validates that the processed data matches the schema contract."""
    # Load schema
    schema = load_schema_contract()
    required_cols = [c['name'] for c in schema['required_columns']]

    # Load a sample processed file (if it exists)
    data_path = os.path.join("data", "processed", "participants_raw.csv")
    if not os.path.exists(data_path):
        pytest.skip("No processed data found to validate against schema.")

    df = pd.read_csv(data_path)

    # Check presence of required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    assert len(missing_cols) == 0, f"Missing required columns: {missing_cols}"

    # Check types (basic check)
    for col in required_cols:
        col_def = next(c for c in schema['required_columns'] if c['name'] == col)
        if col_def['type'] == 'numeric':
            # Check if column is numeric or can be converted
            try:
                pd.to_numeric(df[col], errors='raise')
            except (ValueError, TypeError):
                assert False, f"Column '{col}' is not numeric as required by schema."
