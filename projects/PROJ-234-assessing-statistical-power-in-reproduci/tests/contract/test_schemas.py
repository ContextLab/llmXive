import pytest
import json
import yaml
import os
from pathlib import Path
from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    yaml = YAML()
    yaml.preserve_quotes = True
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.load(f)

def load_json_data(data_path: Path) -> list:
    """Load a JSON data file."""
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_against_schema(data: list, schema: dict):
    """
    Simple validation that data items match the required fields in the schema.
    This is a basic check to ensure structure matches the contract.
    """
    required_fields = schema.get('required', [])
    items_schema = schema.get('items', {})
    properties = items_schema.get('properties', {})

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} is not a dictionary")
        
        for field in required_fields:
            if field not in item:
                raise ValueError(f"Item {i} missing required field: {field}")
        
        # Check types if defined
        for field, field_schema in properties.items():
            if field in item:
                expected_type = field_schema.get('type')
                value = item[field]
                
                if expected_type == 'string' and not isinstance(value, str):
                    raise ValueError(f"Item {i}, field '{field}': expected string, got {type(value)}")
                elif expected_type == 'integer' and not isinstance(value, int):
                    raise ValueError(f"Item {i}, field '{field}': expected integer, got {type(value)}")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    raise ValueError(f"Item {i}, field '{field}': expected number, got {type(value)}")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    raise ValueError(f"Item {i}, field '{field}': expected boolean, got {type(value)}")

@pytest.fixture
def dataset_schema_path():
    return CONTRACTS_DIR / "dataset_metadata.schema.yaml"

@pytest.fixture
def dataset_data_path():
    return DATA_RAW_DIR / "openml_metadata_filtered.json"

@pytest.fixture
def extracted_params_schema_path():
    return CONTRACTS_DIR / "extracted_params.schema.yaml"

@pytest.fixture
def extracted_params_data_path():
    return DATA_PROCESSED_DIR / "extracted_params.json"

def test_dataset_metadata_schema(dataset_schema_path, dataset_data_path):
    """
    Contract test: Validates data/raw/openml_metadata_filtered.json 
    against contracts/dataset_metadata.schema.yaml.
    """
    # Check if files exist (skipping if not, as per pytest convention for integration)
    if not dataset_schema_path.exists():
        pytest.skip(f"Schema file missing: {dataset_schema_path}")
    if not dataset_data_path.exists():
        pytest.skip(f"Data file missing: {dataset_data_path}. Run code/01_ingest_openml.py first.")

    schema = load_schema(dataset_schema_path)
    data = load_json_data(dataset_data_path)

    if not data:
        pytest.skip("Data file is empty. Run code/01_ingest_openml.py first.")

    validate_against_schema(data, schema)

def test_extracted_params_schema(extracted_params_schema_path, extracted_params_data_path):
    """
    Contract test: Validates data/processed/extracted_params.json 
    against contracts/extracted_params.schema.yaml.
    """
    # Check if files exist
    if not extracted_params_schema_path.exists():
        pytest.skip(f"Schema file missing: {extracted_params_schema_path}")
    if not extracted_params_data_path.exists():
        pytest.skip(f"Data file missing: {extracted_params_data_path}. Run code/02_parse_publications.py first.")

    schema = load_schema(extracted_params_schema_path)
    data = load_json_data(extracted_params_data_path)

    if not data:
        pytest.skip("Data file is empty. Run code/02_parse_publications.py first.")

    validate_against_schema(data, schema)