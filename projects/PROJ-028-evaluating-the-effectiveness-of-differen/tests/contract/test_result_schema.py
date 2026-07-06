"""
Contract test for evaluation result schema validation.

Validates that evaluation results written to data/results/ conform to the
JSON schema defined in specs/001-evaluate-prompting-strategies/contracts/evaluation_result.schema.yaml.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import pytest
import yaml

# Add project root to path for imports if running from tests/
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCHEMA_PATH = (
    PROJECT_ROOT
    / "specs"
    / "001-evaluate-prompting-strategies"
    / "contracts"
    / "evaluation_result.schema.yaml"
)


def load_schema() -> Dict[str, Any]:
    """Load the JSON schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str) -> bool:
    """Validate a value against a JSON schema type."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }
    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        return False
    return isinstance(value, expected_python_type)


def validate_value_against_schema(
    value: Any, schema: Dict[str, Any], path: str = "root"
) -> List[str]:
    """Recursively validate a value against a JSON schema."""
    errors = []

    schema_type = schema.get("type")
    if schema_type:
        if not validate_type(value, schema_type):
            errors.append(
                f"{path}: Expected type '{schema_type}', got '{type(value).__name__}'"
            )
            return errors

    # Validate enum if present
    if "enum" in schema:
        if value not in schema["enum"]:
            errors.append(
                f"{path}: Value '{value}' not in allowed values {schema['enum']}"
            )

    # Validate object properties
    if schema_type == "object" and "properties" in schema:
        if not isinstance(value, dict):
            errors.append(f"{path}: Expected object, got {type(value).__name__}")
            return errors

        # Check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in value:
                errors.append(f"{path}: Missing required field '{field}'")

        # Validate each property
        for prop_name, prop_schema in schema["properties"].items():
            if prop_name in value:
                prop_path = f"{path}.{prop_name}"
                errors.extend(
                    validate_value_against_schema(value[prop_name], prop_schema, prop_path)
                )

    # Validate array items
    if schema_type == "array" and "items" in schema:
        if not isinstance(value, list):
            errors.append(f"{path}: Expected array, got {type(value).__name__}")
            return errors
        items_schema = schema["items"]
        for idx, item in enumerate(value):
            item_path = f"{path}[{idx}]"
            errors.extend(validate_value_against_schema(item, items_schema, item_path))

    return errors


class TestResultSchema:
    """Contract tests for evaluation result schema validation."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the evaluation result schema."""
        return load_schema()

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

    def test_schema_is_valid_yaml(self):
        """Verify the schema file is valid YAML and contains required fields."""
        schema = load_schema()
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "type" in schema, "Schema must have a 'type' field"
        assert schema["type"] == "object", "Root schema type must be 'object'"

    def test_required_fields_present(self, schema: Dict[str, Any]):
        """Verify the schema defines required fields."""
        required = schema.get("required", [])
        assert "task_id" in required, "task_id must be required"
        assert "strategy" in required, "strategy must be required"
        assert "seed" in required, "seed must be required"
        assert "samples" in required, "samples must be required"
        assert "metrics" in required, "metrics must be required"

    def test_validate_valid_result(self, schema: Dict[str, Any]):
        """Validate a properly structured result against the schema."""
        valid_result = {
            "task_id": "mbpp/task_1",
            "strategy": "zero-shot",
            "seed": 42,
            "samples": [
                {
                    "sample_id": 0,
                    "code": "def add(a, b):\n    return a + b",
                    "passed": True,
                    "execution_time": 0.05,
                    "error": None,
                }
            ],
            "metrics": {
                "pass_1": 1.0,
                "pass_10": 1.0,
                "total_samples": 1,
                "passed_samples": 1,
            },
            "metadata": {
                "prompt": "Write a function to add two numbers.",
                "model": "test-model",
            },
        }
        errors = validate_value_against_schema(valid_result, schema)
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_validate_missing_required_field(self, schema: Dict[str, Any]):
        """Validate that missing required fields are caught."""
        invalid_result = {
            "task_id": "mbpp/task_1",
            "strategy": "zero-shot",
            # Missing seed, samples, metrics
        }
        errors = validate_value_against_field(invalid_result, schema)
        assert len(errors) > 0, "Should have validation errors for missing required fields"
        assert any("Missing required field" in e for e in errors)

    def test_validate_wrong_type(self, schema: Dict[str, Any]):
        """Validate that type mismatches are caught."""
        invalid_result = {
            "task_id": 123,  # Should be string
            "strategy": "zero-shot",
            "seed": 42,
            "samples": [],
            "metrics": {},
        }
        errors = validate_value_against_schema(invalid_result, schema)
        assert len(errors) > 0, "Should have validation errors for type mismatch"
        assert any("Expected type 'string'" in e for e in errors)

    def test_validate_enum_value(self, schema: Dict[str, Any]):
        """Validate that invalid enum values are caught."""
        # First, check if strategy has enum defined
        strategy_schema = schema.get("properties", {}).get("strategy", {})
        if "enum" in strategy_schema:
            invalid_result = {
                "task_id": "mbpp/task_1",
                "strategy": "invalid-strategy",  # Not in enum
                "seed": 42,
                "samples": [],
                "metrics": {},
            }
            errors = validate_value_against_schema(invalid_result, schema)
            assert len(errors) > 0, "Should have validation errors for invalid enum value"
            assert any("not in allowed values" in e for e in errors)

    def test_validate_result_file_if_exists(self):
        """Validate any existing result files in data/results/ if they exist."""
        results_dir = PROJECT_ROOT / "data" / "results"
        if not results_dir.exists():
            pytest.skip("Results directory does not exist yet")

        schema = load_schema()
        result_files = list(results_dir.glob("*.json"))
        if not result_files:
            pytest.skip("No result files found in data/results/")

        for result_file in result_files:
            with open(result_file, "r", encoding="utf-8") as f:
                try:
                    result = json.load(f)
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in {result_file}: {e}")

            errors = validate_value_against_schema(result, schema, path=str(result_file))
            if errors:
                pytest.fail(
                    f"Validation errors in {result_file.name}:\n" + "\n".join(errors)
                )