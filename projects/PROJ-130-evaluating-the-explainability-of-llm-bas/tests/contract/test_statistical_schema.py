"""
Contract test for statistical schema.
Validates that statistical artifacts conform to the defined YAML schema.
"""
import pytest

try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

import yaml
from pathlib import Path

from tests.contract.conftest import STATISTICAL_SCHEMA


def load_schema(schema_path: Path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestStatisticalContract:
    """Contract tests for statistical schema."""

    def test_statistical_schema_is_valid(self):
        """Verify the statistical schema file is valid YAML and has structure."""
        schema = load_schema(STATISTICAL_SCHEMA)
        assert schema is not None
        assert isinstance(schema, dict)

    def test_statistical_artifact_conforms(self):
        """
        Test that a valid statistical artifact conforms to the schema.
        Simulates output of T033, T034, T035.
        """
        schema = load_schema(STATISTICAL_SCHEMA)

        valid_statistical = {
            "statistical_results": [
                {
                    "correlation_coeff": 0.654,
                    "auc_roc": 0.782,
                    "p_value": 0.032
                }
            ]
        }

        try:
            validate(instance=valid_statistical, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid statistical artifact failed schema validation: {e.message}")

    def test_missing_p_value_fails(self):
        """Test that missing p_value fails validation."""
        schema = load_schema(STATISTICAL_SCHEMA)

        invalid_statistical = {
            "statistical_results": [
                {
                    "correlation_coeff": 0.654,
                    "auc_roc": 0.782,
                    # "p_value" missing
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_statistical, schema=schema)

    def test_non_numeric_value_fails(self):
        """Test that non-numeric values fail validation."""
        schema = load_schema(STATISTICAL_SCHEMA)

        invalid_statistical = {
            "statistical_results": [
                {
                    "correlation_coeff": "strong",  # Should be float
                    "auc_roc": 0.782,
                    "p_value": 0.032
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_statistical, schema=schema)
