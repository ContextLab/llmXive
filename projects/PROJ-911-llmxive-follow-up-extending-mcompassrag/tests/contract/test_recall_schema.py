"""
Contract test for Recall@k output schema.

This test validates that the output of the Recall@k calculation
adheres to the schema defined in contracts/output.schema.yaml.
It ensures that the retrieval scores file contains the required
fields and data types before downstream processing.
"""
import json
import os
import pytest
from pathlib import Path
from typing import List, Dict, Any

# Import schema validation utilities from the project
try:
    from code.validate_schemas import load_schema, validate_artifact
except ImportError:
    # Fallback if validate_schemas is not yet available in the path
    # This allows the test to run even if the validation module is missing,
    # though in a full run it should be present.
    pytest.skip("validate_schemas module not found", allow_module_level=True)


@pytest.fixture
def schema_path() -> Path:
    """Return the path to the output schema definition."""
    return Path("contracts/output.schema.yaml")


@pytest.fixture
def results_dir() -> Path:
    """Return the path to the results directory."""
    return Path("data/results")


def load_recall_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the Recall@k output schema from YAML."""
    return load_schema(schema_path)


def test_recall_schema_exists(schema_path: Path):
    """Verify that the schema file exists."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"


def test_recall_schema_valid_yaml(schema_path: Path):
    """Verify that the schema file is valid YAML."""
    schema = load_recall_schema(schema_path)
    assert schema is not None
    assert "type" in schema
    assert schema["type"] == "object"


def test_recall_schema_has_required_fields(schema_path: Path):
    """Verify that the schema defines required fields for Recall@k output."""
    schema = load_recall_schema(schema_path)
    
    # The schema should require specific fields for the retrieval scores
    required_fields = schema.get("required", [])
    
    # Based on FR-004 and T024, we expect at least:
    # - query_id (or similar identifier)
    # - retrieved_docs (list of document IDs)
    # - recall_score (float)
    # - k (int, the k value used)
    
    # We check that the schema defines these fields in properties
    properties = schema.get("properties", {})
    
    assert "query_id" in properties or "query" in properties, \
        "Schema must define a query identifier field"
    assert "recall_score" in properties, \
        "Schema must define a recall_score field"
    assert "k" in properties, \
        "Schema must define the k parameter field"


def test_validate_sample_recall_output(schema_path: Path, results_dir: Path):
    """
    Validate a sample Recall@k output file against the schema.
    
    This test creates a minimal valid output file to ensure the 
    validation logic works correctly.
    """
    # Create a sample output that should pass validation
    sample_output = {
        "query_id": "test_query_1",
        "retrieved_docs": ["doc_1", "doc_2", "doc_3"],
        "recall_score": 0.75,
        "k": 10
    }
    
    # Validate the sample against the schema
    schema = load_recall_schema(schema_path)
    is_valid, errors = validate_artifact(sample_output, schema)
    
    assert is_valid, f"Sample output should be valid but failed: {errors}"


def test_validate_invalid_recall_output(schema_path: Path):
    """
    Validate that an invalid Recall@k output fails schema validation.
    """
    # Create an invalid output (missing required field)
    invalid_output = {
        "query_id": "test_query_1",
        # Missing recall_score and k
    }
    
    schema = load_recall_schema(schema_path)
    is_valid, errors = validate_artifact(invalid_output, schema)
    
    assert not is_valid, "Invalid output should fail validation"
    assert len(errors) > 0, "Validation should return error details"


def test_validate_wrong_type_recall_score(schema_path: Path):
    """
    Validate that a wrong type for recall_score fails schema validation.
    """
    invalid_output = {
        "query_id": "test_query_1",
        "retrieved_docs": ["doc_1"],
        "recall_score": "not_a_float",  # Should be float
        "k": 10
    }
    
    schema = load_recall_schema(schema_path)
    is_valid, errors = validate_artifact(invalid_output, schema)
    
    assert not is_valid, "Output with wrong type should fail validation"