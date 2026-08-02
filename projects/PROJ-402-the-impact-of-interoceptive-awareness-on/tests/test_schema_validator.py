"""
Tests for the schema_validator module.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import yaml

# Add project root to path if running standalone
sys_path = Path(__file__).resolve().parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from utils.schema_validator import (
    load_schema_from_file,
    validate_data_against_schema,
    validate_file_against_schema,
    validate_contract_input,
    ContractViolationError
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_schema(temp_dir):
    """Create a sample JSON schema."""
    schema = {
        "type": "object",
        "properties": {
            "subject_id": {"type": "integer"},
            "phase": {"type": "string"},
            "RMSSD": {"type": "number"}
        },
        "required": ["subject_id", "phase", "RMSSD"]
    }
    schema_path = temp_dir / "test_schema.json"
    with open(schema_path, 'w') as f:
        json.dump(schema, f)
    return schema_path


@pytest.fixture
def valid_data():
    """Create valid test data."""
    return {
        "subject_id": 101,
        "phase": "baseline",
        "RMSSD": 45.2
    }


@pytest.fixture
def invalid_data():
    """Create invalid test data (missing required field)."""
    return {
        "subject_id": 101,
        "phase": "baseline"
        # Missing RMSSD
    }


def test_load_schema_from_file_json(temp_dir):
    """Test loading a JSON schema."""
    schema = {"type": "string"}
    path = temp_dir / "schema.json"
    with open(path, 'w') as f:
        json.dump(schema, f)

    loaded = load_schema_from_file(path)
    assert loaded == schema


def test_load_schema_from_file_yaml(temp_dir):
    """Test loading a YAML schema."""
    schema = {"type": "string"}
    path = temp_dir / "schema.yaml"
    with open(path, 'w') as f:
        yaml.dump(schema, f)

    loaded = load_schema_from_file(path)
    assert loaded == schema


def test_load_schema_from_file_not_found():
    """Test error when schema file is missing."""
    with pytest.raises(FileNotFoundError):
        load_schema_from_file("non_existent_schema.json")


def test_validate_data_against_schema_valid(valid_data, sample_schema):
    """Test validation with valid data."""
    schema = load_schema_from_file(sample_schema)
    assert validate_data_against_schema(valid_data, schema) is True


def test_validate_data_against_schema_invalid(valid_data, invalid_data, sample_schema):
    """Test validation with invalid data."""
    schema = load_schema_from_file(sample_schema)
    with pytest.raises(ContractViolationError):
        validate_data_against_schema(invalid_data, schema)


def test_validate_file_against_schema_csv(temp_dir):
    """Test validation of a CSV file against a schema."""
    # Define schema expecting a list of objects
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "subject_id": {"type": "integer"},
                "value": {"type": "number"}
            },
            "required": ["subject_id", "value"]
        }
    }
    schema_path = temp_dir / "csv_schema.json"
    with open(schema_path, 'w') as f:
        json.dump(schema, f)

    # Create valid CSV
    csv_path = temp_dir / "data.csv"
    with open(csv_path, 'w') as f:
        f.write("subject_id,value\n101,45.2\n102,50.1\n")

    assert validate_file_against_schema(csv_path, schema_path) is True


def test_validate_contract_input_missing_schema(temp_dir):
    """Test error when contract schema is missing."""
    data_path = temp_dir / "data.json"
    data_path.write_text("{}")

    with pytest.raises(FileNotFoundError):
        validate_contract_input(data_path, "non_existent_contract", contracts_dir=temp_dir)


def test_validate_contract_input_valid(temp_dir):
    """Test full contract validation flow."""
    # Create schema file
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"]
    }
    schema_path = temp_dir / "my_contract.schema.json"
    with open(schema_path, 'w') as f:
        json.dump(schema, f)

    # Create valid data
    data = {"status": "ok"}
    data_path = temp_dir / "data.json"
    with open(data_path, 'w') as f:
        json.dump(data, f)

    # This should not raise
    result = validate_contract_input(data_path, "my_contract", contracts_dir=temp_dir)
    assert result is True