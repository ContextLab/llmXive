"""
Contract test for correlation_results schema.

Validates that correlation output data conforms to the contract schema
defined in specs/001-evaluate-code-duplication-llm-understanding/contracts/correlation_results.schema.yaml

Per spec.md Independent Test requirements for User Story 2.
"""

import json
import math
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml


def load_schema() -> Dict[str, Any]:
    """Load the correlation results schema from the contracts directory."""
    schema_path = (
        Path(__file__).parent.parent.parent
        / "specs"
        / "001-evaluate-code-duplication-llm-understanding"
        / "contracts"
        / "correlation_results.schema.yaml"
    )
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def validate_field_type(value: Any, expected_type: str, field_name: str) -> None:
    """Validate that a value matches the expected type from schema."""
    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }

    expected = type_map.get(expected_type)
    if expected is None:
        raise ValueError(f"Unknown type: {expected_type}")

    if not isinstance(value, expected):
        raise TypeError(
            f"Field '{field_name}' expected type '{expected_type}', "
            f"got '{type(value).__name__}' with value '{value}'"
        )


def validate_numeric_range(
    value: float, field_name: str, min_val: float, max_val: float
) -> None:
    """Validate that a numeric value is within the expected range."""
    if math.isnan(value) or math.isinf(value):
        raise ValueError(
            f"Field '{field_name}' must be a finite number, got '{value}'"
        )
    if value < min_val or value > max_val:
        raise ValueError(
            f"Field '{field_name}' value '{value}' is outside "
            f"expected range [{min_val}, {max_val}]"
        )


def validate_correlation_record(record: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validate a single correlation result record against the schema."""
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    # Check required fields
    for field in required_fields:
        if field not in record:
            raise AssertionError(
                f"Required field '{field}' missing from correlation record"
            )

    # Validate each field in the record
    for field_name, value in record.items():
        if field_name not in properties:
            raise AssertionError(
                f"Unknown field '{field_name}' in correlation record"
            )

        field_spec = properties[field_name]
        expected_type = field_spec.get("type")

        if expected_type:
            validate_field_type(value, expected_type, field_name)

        # Specific validations for numeric fields
        if field_name == "correlation_coefficient":
            validate_numeric_range(value, field_name, -1.0, 1.0)
        elif field_name == "p_value":
            validate_numeric_range(value, field_name, 0.0, 1.0)
        elif field_name == "sample_size":
            validate_numeric_range(value, field_name, 1, 1000000)


def generate_valid_sample_record() -> Dict[str, Any]:
    """Generate a valid sample correlation record for testing."""
    return {
        "metric_pair": "clone_density_perplexity",
        "correlation_coefficient": -0.42,
        "p_value": 0.003,
        "sample_size": 1000,
        "method": "spearman",
        "threshold": 0.7,
    }


def generate_edge_case_records() -> List[Dict[str, Any]]:
    """Generate edge case records for boundary testing."""
    return [
        # Minimum valid correlation (perfect negative)
        {
            "metric_pair": "clone_density_perplexity",
            "correlation_coefficient": -1.0,
            "p_value": 0.001,
            "sample_size": 500,
            "method": "spearman",
            "threshold": 0.7,
        },
        # Maximum valid correlation (perfect positive)
        {
            "metric_pair": "clone_density_accuracy",
            "correlation_coefficient": 1.0,
            "p_value": 0.001,
            "sample_size": 500,
            "method": "spearman",
            "threshold": 0.9,
        },
        # Zero correlation
        {
            "metric_pair": "clone_density_perplexity",
            "correlation_coefficient": 0.0,
            "p_value": 0.5,
            "sample_size": 1000,
            "method": "spearman",
            "threshold": 0.8,
        },
        # Borderline significance (p = 0.05)
        {
            "metric_pair": "clone_density_accuracy",
            "correlation_coefficient": 0.25,
            "p_value": 0.05,
            "sample_size": 2000,
            "method": "spearman",
            "threshold": 0.7,
        },
    ]


class TestCorrelationSchema:
    """Contract tests for correlation_results schema validation."""

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the correlation results schema."""
        return load_schema()

    def test_schema_exists(self) -> None:
        """Test that the correlation schema file exists and is valid YAML."""
        schema = load_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "type" in schema
        assert schema["type"] == "object"

    def test_schema_has_required_fields(self, schema: Dict[str, Any]) -> None:
        """Test that the schema defines required fields."""
        required = schema.get("required", [])
        assert len(required) > 0, "Schema must have at least one required field"

        # Verify key fields are required
        expected_required = ["metric_pair", "correlation_coefficient", "p_value"]
        for field in expected_required:
            assert field in required, f"Required field '{field}' missing from schema"

    def test_schema_has_properties(self, schema: Dict[str, Any]) -> None:
        """Test that the schema defines properties for correlation metrics."""
        properties = schema.get("properties", {})

        # Verify key properties exist
        expected_properties = [
            "metric_pair",
            "correlation_coefficient",
            "p_value",
            "sample_size",
            "method",
            "threshold",
        ]
        for prop in expected_properties:
            assert prop in properties, f"Property '{prop}' missing from schema"

    def test_validate_valid_record(self, schema: Dict[str, Any]) -> None:
        """Test that a valid record passes validation."""
        record = generate_valid_sample_record()
        # Should not raise any exceptions
        validate_correlation_record(record, schema)

    def test_validate_edge_case_records(self, schema: Dict[str, Any]) -> None:
        """Test that edge case records (boundary values) pass validation."""
        records = generate_edge_case_records()
        for record in records:
            validate_correlation_record(record, schema)

    def test_missing_required_field_raises_error(self, schema: Dict[str, Any]) -> None:
        """Test that missing required fields raise an error."""
        record = generate_valid_sample_record()
        del record["correlation_coefficient"]

        with pytest.raises(AssertionError) as exc_info:
            validate_correlation_record(record, schema)

        assert "correlation_coefficient" in str(exc_info.value)

    def test_invalid_correlation_range_raises_error(
        self, schema: Dict[str, Any]
    ) -> None:
        """Test that correlation outside [-1, 1] raises an error."""
        record = generate_valid_sample_record()
        record["correlation_coefficient"] = 1.5

        with pytest.raises(ValueError) as exc_info:
            validate_correlation_record(record, schema)

        assert "correlation_coefficient" in str(exc_info.value)
        assert "outside" in str(exc_info.value)

    def test_invalid_p_value_range_raises_error(self, schema: Dict[str, Any]) -> None:
        """Test that p-value outside [0, 1] raises an error."""
        record = generate_valid_sample_record()
        record["p_value"] = 1.5

        with pytest.raises(ValueError) as exc_info:
            validate_correlation_record(record, schema)

        assert "p_value" in str(exc_info.value)

    def test_nan_values_raise_error(self, schema: Dict[str, Any]) -> None:
        """Test that NaN values raise an error."""
        record = generate_valid_sample_record()
        record["correlation_coefficient"] = float("nan")

        with pytest.raises(ValueError) as exc_info:
            validate_correlation_record(record, schema)

        assert "finite" in str(exc_info.value)

    def test_inf_values_raise_error(self, schema: Dict[str, Any]) -> None:
        """Test that infinite values raise an error."""
        record = generate_valid_sample_record()
        record["correlation_coefficient"] = float("inf")

        with pytest.raises(ValueError) as exc_info:
            validate_correlation_record(record, schema)

        assert "finite" in str(exc_info.value)

    def test_unknown_field_raises_error(self, schema: Dict[str, Any]) -> None:
        """Test that unknown fields raise an error."""
        record = generate_valid_sample_record()
        record["unknown_field"] = "should_not_exist"

        with pytest.raises(AssertionError) as exc_info:
            validate_correlation_record(record, schema)

        assert "unknown_field" in str(exc_info.value)

    def test_wrong_type_field_raises_error(self, schema: Dict[str, Any]) -> None:
        """Test that wrong type for a field raises an error."""
        record = generate_valid_sample_record()
        record["correlation_coefficient"] = "not_a_number"

        with pytest.raises(TypeError) as exc_info:
            validate_correlation_record(record, schema)

        assert "correlation_coefficient" in str(exc_info.value)

    def test_sample_size_minimum(self, schema: Dict[str, Any]) -> None:
        """Test that sample_size minimum of 1 is enforced."""
        record = generate_valid_sample_record()
        record["sample_size"] = 0

        with pytest.raises(ValueError) as exc_info:
            validate_correlation_record(record, schema)

        assert "sample_size" in str(exc_info.value)

    def test_schema_validates_multiple_metric_pairs(self, schema: Dict[str, Any]) -> None:
        """Test that schema accepts different metric pair combinations."""
        valid_pairs = [
            "clone_density_perplexity",
            "clone_density_accuracy",
            "perplexity_accuracy",
        ]

        for pair in valid_pairs:
            record = generate_valid_sample_record()
            record["metric_pair"] = pair
            validate_correlation_record(record, schema)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
