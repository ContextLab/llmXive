"""
Contract test for dataset schema.
Validates that dataset artifacts conform to the defined YAML schema.
"""
import json
from pathlib import Path
import pytest

try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

import yaml

# Import schema path from conftest
from tests.contract.conftest import DATASET_SCHEMA


def load_schema(schema_path: Path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestDatasetContract:
    """Contract tests for dataset schema."""

    def test_dataset_schema_is_valid(self):
        """Verify the dataset schema file is valid YAML and has structure."""
        schema = load_schema(DATASET_SCHEMA)
        assert schema is not None
        assert isinstance(schema, dict)
        # Check for essential schema keys
        assert "type" in schema or "properties" in schema

    def test_dataset_artifact_conforms(self):
        """
        Test that a valid dataset artifact conforms to the schema.
        This simulates the output of T019 (downloaded data).
        """
        schema = load_schema(DATASET_SCHEMA)

        # Sample valid dataset structure
        dataset_artifact = {
            "bugs": [
                {
                    "id": "Lang-1",
                    "file_path": "src/java/org/apache/lang/Example.java",
                    "test_suite": ["org.apache.lang.TestExample"],
                    "reference_text": "public class Example { }"
                },
                {
                    "id": "Math-5",
                    "file_path": "src/java/org/apache/math/MathUtil.java",
                    "test_suite": ["org.apache.math.TestMathUtil"],
                    "reference_text": "public class MathUtil { }"
                }
            ]
        }

        # This should pass validation
        try:
            validate(instance=dataset_artifact, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid dataset artifact failed schema validation: {e.message}")

    def test_dataset_missing_fields_fails(self):
        """Test that dataset missing required fields fails validation."""
        schema = load_schema(DATASET_SCHEMA)

        # Missing 'file_path'
        invalid_dataset = {
            "bugs": [
                {
                    "id": "Lang-1",
                    # "file_path" missing
                    "test_suite": ["test"],
                    "reference_text": "code"
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_dataset, schema=schema)

    def test_dataset_wrong_type_fails(self):
        """Test that dataset with wrong field types fails validation."""
        schema = load_schema(DATASET_SCHEMA)

        # 'id' should be string, not integer
        invalid_dataset = {
            "bugs": [
                {
                    "id": 12345,
                    "file_path": "path/to/file.java",
                    "test_suite": ["test"],
                    "reference_text": "code"
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_dataset, schema=schema)
