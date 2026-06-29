"""
Contract test for JSON cascade schema validation.

This test validates that JSON cascade files conform to the expected schema
as defined in contracts/cascade_schema.json.

Per T008, JSON schemas are stored in contracts/ directory.
Per T084, sample cascade files exist in data/raw/ for validation testing.
"""
import json
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Import project utilities
from pipeline.utils import set_global_seed, setup_logger

# Set global seed for reproducibility
set_global_seed(12345)
logger = setup_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Schema file path
CASCADE_SCHEMA_PATH = CONTRACTS_DIR / "cascade_schema.json"

def load_schema(schema_path: Path) -> dict:
    """Load JSON schema from file."""
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_cascade_json(cascade_path: Path) -> dict:
    """Load a cascade JSON file."""
    with open(cascade_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_schema_file_exists():
    """Contract test: cascade schema file must exist in contracts/."""
    assert CASCADE_SCHEMA_PATH.exists(), (
        f"Cascade schema file not found at {CASCADE_SCHEMA_PATH}. "
        "Run T008 to create contract schemas."
    )

def test_schema_is_valid_json():
    """Contract test: cascade schema must be valid JSON."""
    schema = load_schema(CASCADE_SCHEMA_PATH)
    assert isinstance(schema, dict), "Schema must be a JSON object"
    assert "$schema" in schema, "Schema must declare $schema version"
    assert "type" in schema, "Schema must declare type"
    assert schema["type"] == "object", "Cascade schema root must be an object"

def test_schema_has_required_properties():
    """Contract test: schema must define required cascade properties."""
    schema = load_schema(CASCADE_SCHEMA_PATH)
    properties = schema.get("properties", {})

    # Required fields per data-model.md and T080
    required_fields = ["cascade_id", "nodes", "edges"]
    for field in required_fields:
        assert field in properties, (
            f"Schema must define required field: {field}"
        )

def test_sample_cascade_validates():
    """Contract test: sample cascade files in data/raw/ must validate."""
    # T084 created sample cascade files in data/raw/
    if not DATA_RAW_DIR.exists():
        pytest.skip("data/raw/ directory not found - T084 not complete")

    schema = load_schema(CASCADE_SCHEMA_PATH)
    validator = Draft7Validator(schema)

    cascade_files = list(DATA_RAW_DIR.glob("*.json"))
    if not cascade_files:
        pytest.skip("No JSON cascade files found in data/raw/")

    for cascade_file in cascade_files:
        logger.info(f"Validating cascade file: {cascade_file.name}")
        cascade_data = load_cascade_json(cascade_file)

        errors = list(validator.iter_errors(cascade_data))
        assert len(errors) == 0, (
            f"Cascade file {cascade_file.name} failed schema validation. "
            f"Errors: {[e.message for e in errors]}"
        )

def test_cascade_nodes_structure():
    """Contract test: cascade nodes must have required fields."""
    schema = load_schema(CASCADE_SCHEMA_PATH)

    # Check nodes items schema
    nodes_schema = schema.get("properties", {}).get("nodes", {})
    items = nodes_schema.get("items", {})
    node_properties = items.get("properties", {})

    required_node_fields = ["node_id", "timestamp", "cascade_id"]
    for field in required_node_fields:
        assert field in node_properties, (
            f"Node schema must define required field: {field}"
        )

def test_cascade_edges_structure():
    """Contract test: cascade edges must have required fields."""
    schema = load_schema(CASCADE_SCHEMA_PATH)

    # Check edges items schema
    edges_schema = schema.get("properties", {}).get("edges", {})
    items = edges_schema.get("items", {})
    edge_properties = items.get("properties", {})

    required_edge_fields = ["source", "target"]
    for field in required_edge_fields:
        assert field in edge_properties, (
            f"Edge schema must define required field: {field}"
        )

def test_invalid_cascade_rejected():
    """Contract test: invalid cascade data must be rejected."""
    schema = load_schema(CASCADE_SCHEMA_PATH)
    validator = Draft7Validator(schema)

    # Create intentionally invalid cascade data
    invalid_cascade = {
        "cascade_id": 123,  # Should be string
        "nodes": "not_an_array",  # Should be array
        "edges": []
    }

    errors = list(validator.iter_errors(invalid_cascade))
    assert len(errors) > 0, "Invalid cascade should produce validation errors"

def test_cascade_id_type():
    """Contract test: cascade_id must be a string."""
    schema = load_schema(CASCADE_SCHEMA_PATH)
    properties = schema.get("properties", {})
    cascade_id_schema = properties.get("cascade_id", {})

    assert cascade_id_schema.get("type") == "string", (
        "cascade_id must be of type string"
    )

def test_timestamp_format():
    """Contract test: timestamp fields must have format specification."""
    schema = load_schema(CASCADE_SCHEMA_PATH)
    nodes_schema = schema.get("properties", {}).get("nodes", {})
    items = nodes_schema.get("items", {})
    node_properties = items.get("properties", {})

    # Per T070, timestamps must be normalized to UTC
    timestamp_schema = node_properties.get("timestamp", {})
    assert timestamp_schema.get("format") == "date-time", (
        "Timestamp must have date-time format for UTC normalization"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
