import json
import jsonschema
import pandas as pd
import pytest
import yaml
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-predicting-molecular-properties-from-top" / "contracts"
DATA_DIR = PROJECT_ROOT / "data" / "processed"

def _load_schema() -> dict:
    schema_path = CONTRACTS_DIR / "feature_matrix.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def _load_features() -> pd.DataFrame:
    # The baseline 10x10 persistence image CSV
    csv_path = DATA_DIR / "topological_features_10x10.csv"
    return pd.read_csv(csv_path)

def test_feature_matrix_schema():
    schema = _load_schema()
    validator = jsonschema.Draft7Validator(schema)

    df = _load_features()
    # Build a record for each row according to the schema
    for _, row in df.iterrows():
        record = {
            "molecule_id": str(row["molecule_id"]),
            "target_property": row["target_property"],
            "target_value": float(row["target_value"]),
        }
        # Add pixel features
        pixel_cols = [c for c in df.columns if c.startswith("pixel_")]
        for col in pixel_cols:
            record[col] = float(row[col])
        # Validate
        validator.validate(record)

def test_feature_matrix_dimensions():
    df = _load_features()
    # Must contain molecule_id, target_property, target_value + 100 pixel columns for 10x10
    expected_pixel_cols = 10 * 10
    pixel_cols = [c for c in df.columns if c.startswith("pixel_")]
    assert len(pixel_cols) == expected_pixel_cols, f"Expected {expected_pixel_cols} pixel columns, got {len(pixel_cols)}"
    # Row count must match filtered_esol.csv
    filtered_path = DATA_DIR.parent / "processed" / "filtered_esol.csv"
    filtered_df = pd.read_csv(filtered_path)
    assert df.shape[0] == filtered_df.shape[0], "Row count mismatch between TDA features and filtered ESOL"

def test_feature_matrix_no_nans():
    df = _load_features()
    assert not df.isnull().any().any(), "Feature matrix contains NaN values"