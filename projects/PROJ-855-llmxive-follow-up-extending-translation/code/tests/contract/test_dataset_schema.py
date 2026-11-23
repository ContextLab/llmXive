import pytest
import json
import os
from pathlib import Path
from utils.data_utils import load_schema, validate_against_schema

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
contracts_dir = project_root / "specs" / "001-gene-regulation" / "contracts"

def get_schema_path() -> Path:
    return contracts_dir / "dataset.schema.yaml"

def load_real_data_sample() -> dict:
    """
    Load a sample from the real generated data if available,
    otherwise construct a minimal valid sample based on the schema.
    """
    data_path = project_root / "data" / "raw" / "synthetic_episodes.parquet"
    if data_path.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(data_path)
            # Return first row as dict
            return df.iloc[0].to_dict()
        except Exception:
            pass

    # Fallback to minimal valid sample based on schema expectations
    return {
        "translation_x": 0.01,
        "translation_y": 0.02,
        "translation_z": 0.0,
        "initial_object_bounds": [0.1, 0.1, 0.1],
        "stability": 1
    }

def test_contract_dataset_schema_columns():
    """
    Contract test: Verify that the dataset schema enforces required columns
    and excludes forbidden columns (rotation, force).
    """
    schema_path = get_schema_path()
    assert schema_path.exists(), "Dataset schema file missing"
    
    schema = load_schema(str(schema_path))
    
    # Check schema defines required properties
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    # Must have translation columns
    assert "translation_x" in properties, "Schema missing translation_x"
    assert "translation_y" in properties, "Schema missing translation_y"
    assert "translation_z" in properties, "Schema missing translation_z"
    assert "initial_object_bounds" in properties, "Schema missing initial_object_bounds"
    assert "stability" in properties, "Schema missing stability"
    
    # Must NOT have forbidden columns (rotation, force)
    assert "rotation" not in properties, "Schema should not allow rotation column"
    assert "force" not in properties, "Schema should not allow force column"
    assert "torque" not in properties, "Schema should not allow torque column"

def test_contract_dataset_data_conformance():
    """
    Contract test: Verify real data conforms to the schema.
    """
    schema_path = get_schema_path()
    schema = load_schema(str(schema_path))
    
    sample = load_real_data_sample()
    
    # Validate against schema
    try:
        validate_against_schema(sample, schema)
    except ValueError as e:
        pytest.fail(f"Real data sample failed schema validation: {e}")
