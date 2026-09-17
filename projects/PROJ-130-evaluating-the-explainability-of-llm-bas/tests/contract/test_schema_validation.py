"""
Contract test framework to validate data artifacts against YAML schemas.
Uses jsonschema to validate JSON data against JSON Schema definitions
derived from the project's YAML schemas.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

# Ensure project root is in path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

from tests.contract.conftest import (
    DATASET_SCHEMA,
    PATCH_SCHEMA,
    CORRECTNESS_SCHEMA,
    EXPLAINABILITY_SCHEMA,
    STATISTICAL_SCHEMA,
)


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema and convert it to a JSON Schema compatible format."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_dict = yaml.safe_load(f)

    # Basic validation that it looks like a schema
    if not isinstance(schema_dict, dict):
        raise ValueError(f"Schema at {schema_path} is not a valid YAML dictionary")

    return schema_dict


def load_json_data(data_path: Path) -> Dict[str, Any]:
    """Load JSON data for validation."""
    if not data_path.exists():
        # Return empty dict if file doesn't exist yet (tests might create it)
        return {}
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestSchemaValidationFramework:
    """Tests to verify the contract test framework itself works."""

    def test_schema_files_exist(self):
        """Verify that all required schema files exist."""
        schemas = [
            DATASET_SCHEMA,
            PATCH_SCHEMA,
            CORRECTNESS_SCHEMA,
            EXPLAINABILITY_SCHEMA,
            STATISTICAL_SCHEMA,
        ]
        for schema_path in schemas:
            assert schema_path.exists(), f"Schema file missing: {schema_path}"

    def test_schemas_are_valid_yaml(self):
        """Verify that all schema files are valid YAML."""
        schemas = [
            DATASET_SCHEMA,
            PATCH_SCHEMA,
            CORRECTNESS_SCHEMA,
            EXPLAINABILITY_SCHEMA,
            STATISTICAL_SCHEMA,
        ]
        for schema_path in schemas:
            schema = load_schema(schema_path)
            assert schema is not None
            assert isinstance(schema, dict)

    def test_schema_has_required_keys(self):
        """Verify schemas have at least basic schema structure."""
        schemas = [
            DATASET_SCHEMA,
            PATCH_SCHEMA,
            CORRECTNESS_SCHEMA,
            EXPLAINABILITY_SCHEMA,
            STATISTICAL_SCHEMA,
        ]
        for schema_path in schemas:
            schema = load_schema(schema_path)
            # At minimum, a schema should have a $schema or type definition
            # or properties for object validation
            has_structure = (
                "$schema" in schema
                or "type" in schema
                or "properties" in schema
            )
            assert has_structure, f"Schema {schema_path} lacks basic structure"


class TestDatasetSchema:
    """Tests for dataset schema validation."""

    def test_valid_dataset_data(self):
        """Test validation of valid dataset structure."""
        schema = load_schema(DATASET_SCHEMA)
        valid_data = {
            "bugs": [
                {
                    "id": "Lang-1",
                    "file_path": "src/main/java/Example.java",
                    "test_suite": ["test1", "test2"],
                    "reference_text": "Original code text"
                }
            ]
        }
        # This should not raise
        validate(instance=valid_data, schema=schema)

    def test_invalid_dataset_data(self):
        """Test that invalid data raises ValidationError."""
        schema = load_schema(DATASET_SCHEMA)
        invalid_data = {
            "bugs": [
                {
                    "id": 123,  # Should be string
                    "file_path": "src/main/java/Example.java",
                    "test_suite": ["test1"],
                    "reference_text": "Original code text"
                }
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)


class TestPatchSchema:
    """Tests for patch schema validation."""

    def test_valid_patch_data(self):
        """Test validation of valid patch structure."""
        schema = load_schema(PATCH_SCHEMA)
        valid_data = {
            "patches": [
                {
                    "id": "patch-Lang-1",
                    "bug_id": "Lang-1",
                    "diff_content": "--- a/file.java\n+++ b/file.java\n@@ -1,3 +1,3 @@\n- old\n+ new",
                    "rationale_text": "This fixes the null pointer exception."
                }
            ]
        }
        validate(instance=valid_data, schema=schema)

    def test_invalid_patch_data(self):
        """Test that invalid patch data raises ValidationError."""
        schema = load_schema(PATCH_SCHEMA)
        invalid_data = {
            "patches": [
                {
                    "id": "patch-Lang-1",
                    "bug_id": 123,  # Should be string
                    "diff_content": "...",
                    "rationale_text": "..."
                }
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)


class TestCorrectnessSchema:
    """Tests for correctness schema validation."""

    def test_valid_correctness_data(self):
        """Test validation of valid correctness structure."""
        schema = load_schema(CORRECTNESS_SCHEMA)
        valid_data = {
            "correctness_results": [
                {
                    "bug_id": "Lang-1",
                    "pass_fail": "pass",
                    "unsafe_flag": False
                }
            ]
        }
        validate(instance=valid_data, schema=schema)

    def test_invalid_correctness_data(self):
        """Test that invalid correctness data raises ValidationError."""
        schema = load_schema(CORRECTNESS_SCHEMA)
        invalid_data = {
            "correctness_results": [
                {
                    "bug_id": "Lang-1",
                    "pass_fail": "invalid_status",  # Should be 'pass' or 'fail'
                    "unsafe_flag": False
                }
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)


class TestExplainabilitySchema:
    """Tests for explainability schema validation."""

    def test_valid_explainability_data(self):
        """Test validation of valid explainability structure."""
        schema = load_schema(EXPLAINABILITY_SCHEMA)
        valid_data = {
            "explainability_results": [
                {
                    "bug_id": "Lang-1",
                    "attention_score": 0.85,
                    "saliency_score": 0.72,
                    "coherence_score": 0.91
                }
            ]
        }
        validate(instance=valid_data, schema=schema)

    def test_invalid_explainability_data(self):
        """Test that invalid explainability data raises ValidationError."""
        schema = load_schema(EXPLAINABILITY_SCHEMA)
        invalid_data = {
            "explainability_results": [
                {
                    "bug_id": "Lang-1",
                    "attention_score": "high",  # Should be float
                    "saliency_score": 0.72,
                    "coherence_score": 0.91
                }
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)


class TestStatisticalSchema:
    """Tests for statistical schema validation."""

    def test_valid_statistical_data(self):
        """Test validation of valid statistical structure."""
        schema = load_schema(STATISTICAL_SCHEMA)
        valid_data = {
            "statistical_results": [
                {
                    "correlation_coeff": 0.65,
                    "auc_roc": 0.78,
                    "p_value": 0.03
                }
            ]
        }
        validate(instance=valid_data, schema=schema)

    def test_invalid_statistical_data(self):
        """Test that invalid statistical data raises ValidationError."""
        schema = load_schema(STATISTICAL_SCHEMA)
        invalid_data = {
            "statistical_results": [
                {
                    "correlation_coeff": 0.65,
                    "auc_roc": 0.78,
                    "p_value": "significant"  # Should be float
                }
            ]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_data, schema=schema)


# Utility function for external use in other test files
def validate_against_schema(data: Dict[str, Any], schema_path: Path) -> bool:
    """
    Generic validation helper.
    Returns True if valid, raises ValidationError if invalid.
    """
    schema = load_schema(schema_path)
    validate(instance=data, schema=schema)
    return True
