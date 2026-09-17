"""
Contract test for patch schema.
Validates that patch artifacts conform to the defined YAML schema.
"""
import pytest

try:
    from jsonschema import validate, ValidationError
except ImportError:
    pytest.skip("jsonschema not installed", allow_module_level=True)

import yaml
from pathlib import Path

from tests.contract.conftest import PATCH_SCHEMA


def load_schema(schema_path: Path):
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestPatchContract:
    """Contract tests for patch schema."""

    def test_patch_schema_is_valid(self):
        """Verify the patch schema file is valid YAML and has structure."""
        schema = load_schema(PATCH_SCHEMA)
        assert schema is not None
        assert isinstance(schema, dict)

    def test_patch_artifact_conforms(self):
        """
        Test that a valid patch artifact conforms to the schema.
        Simulates output of T020 (patch generation).
        """
        schema = load_schema(PATCH_SCHEMA)

        valid_patch = {
            "patches": [
                {
                    "id": "patch-Lang-1-v1",
                    "bug_id": "Lang-1",
                    "diff_content": "--- a/Example.java\n+++ b/Example.java\n@@ -1,5 +1,5 @@\n- return null;\n+ return fixed_value;",
                    "rationale_text": "Replaced null return with fixed value to prevent NPE."
                }
            ]
        }

        try:
            validate(instance=valid_patch, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Valid patch artifact failed schema validation: {e.message}")

    def test_patch_missing_diff_fails(self):
        """Test that patch missing diff_content fails validation."""
        schema = load_schema(PATCH_SCHEMA)

        invalid_patch = {
            "patches": [
                {
                    "id": "patch-Lang-1-v1",
                    "bug_id": "Lang-1",
                    # "diff_content" missing
                    "rationale_text": "Some rationale."
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_patch, schema=schema)

    def test_patch_missing_rationale_fails(self):
        """Test that patch missing rationale_text fails validation."""
        schema = load_schema(PATCH_SCHEMA)

        invalid_patch = {
            "patches": [
                {
                    "id": "patch-Lang-1-v1",
                    "bug_id": "Lang-1",
                    "diff_content": "--- a/file.java\n+++ b/file.java",
                    # "rationale_text" missing
                }
            ]
        }

        with pytest.raises(ValidationError):
            validate(instance=invalid_patch, schema=schema)
