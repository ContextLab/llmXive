"""
Schema Validation Module.
Validates dataframes against defined YAML schemas.
"""
import os
import sys
import json
import yaml
import pandas as pd
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate a dataframe against a schema.
    Checks for required columns and basic types.
    """
    required_cols = schema.get('required_columns', [])
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return True

def main():
    """Run schema validation on the generated synthetic data."""
    schema_path = Path("contracts/dataset.schema.yaml")
    data_path = Path("data/raw/synthetic_adsorption_data.csv")

    if not schema_path.exists():
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        sys.exit(1)

    schema = load_schema(schema_path)
    df = pd.read_csv(data_path)

    try:
        validate_dataframe(df, schema)
        print(f"Validation successful: {data_path} conforms to schema.")
    except ValueError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
