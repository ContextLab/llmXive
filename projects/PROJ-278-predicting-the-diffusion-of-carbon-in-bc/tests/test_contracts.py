import pytest
import yaml
import json
import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, ValidationError
import jsonschema

def load_schema(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(json_path, schema_path):
    schema = load_schema(schema_path)
    with open(json_path, 'r') as f:
        data = json.load(f)
    jsonschema.validate(instance=data, schema=schema)

def validate_csv_against_schema(csv_path, schema_path):
    # Basic validation: check columns exist
    schema = load_schema(schema_path)
    df = pd.read_csv(csv_path)
    required_cols = schema.get('required', [])
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"

def test_model_output_schema():
    schema_path = Path(__file__).parent.parent / "contracts" / "model_output.schema.yaml"
    results_path = Path(__file__).parent.parent / "data" / "outputs" / "model_results.json"
    
    if not schema_path.exists():
        pytest.fail("Schema file not found: model_output.schema.yaml")
    
    if not results_path.exists():
        pytest.skip("model_results.json not found yet (training may not have run).")
    
    try:
        validate_json_against_schema(str(results_path), str(schema_path))
    except jsonschema.ValidationError as e:
        pytest.fail(f"Validation failed: {e.message}")

def test_dataset_schema():
    schema_path = Path(__file__).parent.parent / "contracts" / "dataset.schema.yaml"
    data_path = Path(__file__).parent.parent / "data" / "processed" / "dataset_cleaned.csv"
    
    if not schema_path.exists():
        pytest.fail("Schema file not found: dataset.schema.yaml")
    
    if not data_path.exists():
        pytest.skip("dataset_cleaned.csv not found yet (preprocessing may not have run).")
    
    try:
        validate_csv_against_schema(str(data_path), str(schema_path))
    except AssertionError as e:
        pytest.fail(f"Validation failed: {e}")