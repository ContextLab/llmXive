"""
Contract test for correctness schema.
Validates that correctness artifacts conform to the defined YAML schema.
"""
import pytest

try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

import yaml
from pathlib import Path

from tests.contract.conftest import CORRECTNESS_SCHEMA


def load_schema(schema_path: Path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestCorrectnessContract:
    """Contract tests for correctness schema."""

    def test_correctness_schema_is_valid(self):
        """Verify the correctness schema file is valid YAML and has structure."""
        schema = load_schema(CORRECTNESS_SCHEMA)
        assert schema is not None
        assert isinstance(schema, dict)

    def test_correctness_artifact_conforms(self):
        """
        Test that a valid correctness artifact conforms to the schema.
        Simulates output of T021 (test execution).
        """
        schema = load_schema(CORRECTNESS_SCHEMA)

        valid_correctness = {
            "correctness_results": [
                {
                    "bug_id": "Lang-1",
                    "pass_fail": "pass",
                    "unsafe_flag": False
                },
                {
                    "bug_id": "Math-5",
                    "pass_fail": "fail",
                    "unsafe_flag": True
                }
            ]
        }

        try:
            validate(instance=valid_correctness, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid correctness artifact failed schema validation: {e.message}")

    def test_invalid_pass_fail_value_fails(self):
        """Test that invalid pass_fail value fails validation."""
        schema = load_schema(CORRECTNESS_SCHEMA)

        invalid_correctness = {
            "correctness_results": [
                {
                    "bug_id": "Lang-1",
                    "pass_fail": "passed",  # Should be 'pass' or 'fail'
                    "unsafe_flag": False
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_correctness, schema=schema)

    def test_missing_bug_id_fails(self):
        """Test that missing bug_id fails validation."""
        schema = load_schema(CORRECTNESS_SCHEMA)

        invalid_correctness = {
            "correctness_results": [
                {
                    # "bug_id" missing
                    "pass_fail": "pass",
                    "unsafe_flag": False
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_correctness, schema=schema)
