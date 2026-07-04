"""
Contract test for manifest schema compliance (T061).
Verifies that output/manifest.json conforms to contracts/manifest.schema.yaml.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Import schema validation utilities from the project
from code.src.contracts.validation import SchemaValidator


def get_manifest_path() -> Path:
    """Return the path to the manifest.json file."""
    return Path("output/manifest.json")


def get_manifest_schema_path() -> Path:
    """Return the path to the manifest schema file."""
    return Path("contracts/manifest.schema.yaml")


def load_manifest() -> Dict[str, Any]:
    """Load and return the manifest.json contents."""
    path = get_manifest_path()
    if not path.exists():
        pytest.fail(f"Manifest file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_manifest_schema() -> Dict[str, Any]:
    """Load and return the manifest schema definition."""
    path = get_manifest_schema_path()
    if not path.exists():
        pytest.fail(f"Manifest schema file not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        import yaml
        return yaml.safe_load(f)


class TestManifestSchemaCompliance:
    """Unit tests verifying manifest.json matches its schema."""

    def test_manifest_file_exists(self):
        """Verify manifest.json exists before schema checks."""
        assert get_manifest_path().exists(), "manifest.json must exist"

    def test_manifest_schema_exists(self):
        """Verify manifest schema exists before validation."""
        assert get_manifest_schema_path().exists(), "manifest schema must exist"

    def test_manifest_loads_valid_json(self):
        """Verify manifest.json is valid JSON."""
        try:
            load_manifest()
        except json.JSONDecodeError as e:
            pytest.fail(f"manifest.json is not valid JSON: {e}")

    def test_manifest_validates_against_schema(self):
        """Verify manifest.json conforms to contracts/manifest.schema.yaml."""
        manifest = load_manifest()
        schema = load_manifest_schema()

        validator = SchemaValidator(schema)
        errors = list(validator.validate(manifest))

        if errors:
            error_msgs = [str(err) for err in errors]
            pytest.fail(f"Manifest schema validation failed:\n" + "\n".join(error_msgs))


class TestManifestSchemaIntegration:
    """Integration tests for manifest schema compliance."""

    def test_manifest_structure_compliance(self):
        """Verify manifest has required top-level keys per schema."""
        manifest = load_manifest()

        # Basic structural checks before full schema validation
        required_keys = ["generated_at", "files"]
        for key in required_keys:
            assert key in manifest, f"Manifest missing required key: {key}"

        assert isinstance(manifest["files"], dict), "manifest['files'] must be a dict"

        # Each file entry should have 'path' and 'sha256'
        for file_entry in manifest["files"].values():
            assert "path" in file_entry, "File entry missing 'path'"
            assert "sha256" in file_entry, "File entry missing 'sha256'"
            assert len(file_entry["sha256"]) == 64, f"Invalid SHA256 length for {file_entry['path']}"

    def test_manifest_schema_validation_integration(self):
        """Full integration: load, validate, and assert compliance."""
        manifest = load_manifest()
        schema = load_manifest_schema()

        validator = SchemaValidator(schema)
        is_valid, errors = validator.validate_full(manifest)

        assert is_valid, f"Manifest failed schema validation: {errors}"