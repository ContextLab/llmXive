"""
Contract test for explainability schema.
Validates that explainability artifacts conform to the defined YAML schema.
"""
import pytest

try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

import yaml
from pathlib import Path

from tests.contract.conftest import EXPLAINABILITY_SCHEMA


def load_schema(schema_path: Path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestExplainabilityContract:
    """Contract tests for explainability schema."""

    def test_explainability_schema_is_valid(self):
        """Verify the explainability schema file is valid YAML and has structure."""
        schema = load_schema(EXPLAINABILITY_SCHEMA)
        assert schema is not None
        assert isinstance(schema, dict)

    def test_explainability_artifact_conforms(self):
        """
        Test that a valid explainability artifact conforms to the schema.
        Simulates output of T027, T028, T029.
        """
        schema = load_schema(EXPLAINABILITY_SCHEMA)

        valid_explainability = {
            "explainability_results": [
                {
                    "bug_id": "Lang-1",
                    "attention_score": 0.854,
                    "saliency_score": 0.723,
                    "coherence_score": 0.912
                }
            ]
        }

        try:
            validate(instance=valid_explainability, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid explainability artifact failed schema validation: {e.message}")

    def test_missing_attention_score_fails(self):
        """Test that missing attention_score fails validation."""
        schema = load_schema(EXPLAINABILITY_SCHEMA)

        invalid_explainability = {
            "explainability_results": [
                {
                    "bug_id": "Lang-1",
                    # "attention_score" missing
                    "saliency_score": 0.723,
                    "coherence_score": 0.912
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_explainability, schema=schema)

    def test_non_float_score_fails(self):
        """Test that non-float score values fail validation."""
        schema = load_schema(EXPLAINABILITY_SCHEMA)

        invalid_explainability = {
            "explainability_results": [
                {
                    "bug_id": "Lang-1",
                    "attention_score": "high",  # Should be float
                    "saliency_score": 0.723,
                    "coherence_score": 0.912
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_explainability, schema=schema)
