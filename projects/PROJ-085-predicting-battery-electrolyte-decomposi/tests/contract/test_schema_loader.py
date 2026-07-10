import pytest
import json
import os
from pathlib import Path
import tempfile
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(project_root))

from tests.contract.schema_loader import (
    load_schema,
    validate_against_schema,
    load_and_validate_dataset_schema,
    load_and_validate_model_output_schema
)

@pytest.fixture
def temp_schema_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["name"]
        }, f)
        path = f.name
    yield path
    os.unlink(path)

def test_load_schema_json(temp_schema_file):
    schema = load_schema(temp_schema_file)
    assert schema["type"] == "object"
    assert "name" in schema["properties"]

def test_validate_against_schema_valid():
    data = {"name": "test", "value": 10}
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "number"}
        },
        "required": ["name"]
    }
    errors = validate_against_schema(data, schema)
    assert len(errors) == 0

def test_validate_against_schema_invalid():
    data = {"name": 123} # name should be string
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    }
    errors = validate_against_schema(data, schema)
    assert len(errors) > 0
    assert "name" in errors[0]

def test_validate_against_schema_missing_required():
    data = {"value": 10}
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"}
        },
        "required": ["name"]
    }
    errors = validate_against_schema(data, schema)
    assert len(errors) > 0
    assert "Missing required field: name" in errors[0]

def test_load_and_validate_dataset_schema(tmp_path):
    # Create a valid CSV
    csv_path = tmp_path / "valid.csv"
    df = pd.DataFrame([{"molecule_id": "1", "smiles": "C"}])
    df.to_csv(csv_path, index=False)

    # Create a basic schema file in contracts
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir(exist_ok=True)
    schema_path = contracts_dir / "dataset.schema.yaml"
    schema_path.write_text("""
    type: array
    items:
      type: object
      properties:
        molecule_id:
          type: string
        smiles:
          type: string
      required:
        - molecule_id
    """)

    try:
        result = load_and_validate_dataset_schema(str(csv_path))
        assert result is True
    finally:
        if schema_path.exists():
            schema_path.unlink()

def test_load_and_validate_model_output_schema(tmp_path):
    json_path = tmp_path / "model.json"
    data = [{"molecule_id": "1", "predicted_energy": 0.5, "potential_v": 0}]
    with open(json_path, 'w') as f:
        json.dump(data, f)

    # Create a basic schema
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir(exist_ok=True)
    schema_path = contracts_dir / "model_output.schema.yaml"
    schema_path.write_text("""
    type: array
    items:
      type: object
      properties:
        molecule_id:
          type: string
        predicted_energy:
          type: number
      required:
        - molecule_id
        - predicted_energy
    """)

    try:
        result = load_and_validate_model_output_schema(str(json_path))
        assert result is True
    finally:
        if schema_path.exists():
            schema_path.unlink()
