import pytest
import yaml
from pathlib import Path

def test_dataset_schema_exists():
    """Verify the contract file exists at the expected path."""
    schema_path = Path("contracts/dataset.schema.yaml")
    assert schema_path.exists(), "contracts/dataset.schema.yaml must exist"

def test_dataset_schema_valid_yaml():
    """Verify the contract file is valid YAML."""
    schema_path = Path("contracts/dataset.schema.yaml")
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in dataset.schema.yaml: {e}")

def test_dataset_schema_required_fields():
    """Verify the schema defines all required fields for CodeSnippet."""
    schema_path = Path("contracts/dataset.schema.yaml")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    required_fields = ["id", "language", "source_code", "ground_truth_label", "ground_truth_category"]
    properties = schema.get("properties", {})
    
    for field in required_fields:
        assert field in properties, f"Required field '{field}' is missing from schema properties"

def test_dataset_schema_type_definitions():
    """Verify type definitions for key fields."""
    schema_path = Path("contracts/dataset.schema.yaml")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    properties = schema.get("properties", {})
    
    # Check id is string
    assert properties["id"]["type"] == "string"
    
    # Check language is string with enum
    assert properties["language"]["type"] == "string"
    assert "enum" in properties["language"]
    
    # Check source_code is string
    assert properties["source_code"]["type"] == "string"
    
    # Check ground_truth_label is string with enum
    assert properties["ground_truth_label"]["type"] == "string"
    assert "enum" in properties["ground_truth_label"]
    
    # Check ground_truth_category is string
    assert properties["ground_truth_category"]["type"] == "string"

def test_dataset_schema_no_additional_properties():
    """Verify the schema prevents additional properties to enforce strict contract."""
    schema_path = Path("contracts/dataset.schema.yaml")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    assert schema.get("additionalProperties") == False, "Schema must forbid additional properties"