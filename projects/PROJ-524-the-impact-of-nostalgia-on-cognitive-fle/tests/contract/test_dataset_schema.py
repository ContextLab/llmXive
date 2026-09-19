import pytest
import yaml
from pathlib import Path

def test_dataset_schema_exists():
    """Verify that the dataset schema file exists."""
    schema_path = Path("contracts/dataset.schema.yaml")
    assert schema_path.exists(), f"Schema file not found at {schema_path}"

def test_dataset_schema_valid_yaml():
    """Verify that the dataset schema is valid YAML."""
    schema_path = Path("contracts/dataset.schema.yaml")
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in dataset schema: {e}")

def test_dataset_schema_required_fields():
    """Verify that all required fields are present in the schema."""
    schema_path = Path("contracts/dataset.schema.yaml")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    required_fields = ["participant_id", "age", "stimulus_type", "perseverative_errors", "categories_completed"]
    properties = schema.get("properties", {})
    
    missing = [f for f in required_fields if f not in properties]
    assert not missing, f"Missing required fields in schema: {missing}"

def test_dataset_schema_optional_mmse():
    """Verify that MMSE is defined as optional (allows null)."""
    schema_path = Path("contracts/dataset.schema.yaml")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    properties = schema.get("properties", {})
    assert "MMSE" in properties, "MMSE field is missing from schema"
    
    mmse_def = properties["MMSE"]
    # MMSE should be either integer or null
    field_type = mmse_def.get("type")
    is_optional = False
    if isinstance(field_type, list):
        is_optional = "null" in field_type
    elif field_type == "null":
        is_optional = True
    
    assert is_optional, "MMSE should be defined as optional (allowing null values)"

def test_output_schema_exists():
    """Verify that the output schema file exists."""
    schema_path = Path("contracts/output.schema.yaml")
    assert schema_path.exists(), f"Output schema file not found at {schema_path}"

def test_output_schema_valid_yaml():
    """Verify that the output schema is valid YAML."""
    schema_path = Path("contracts/output.schema.yaml")
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in output schema: {e}")