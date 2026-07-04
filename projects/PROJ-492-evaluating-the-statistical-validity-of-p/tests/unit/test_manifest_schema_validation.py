"""
Unit tests for manifest schema validation.

Tests the manifest_schema_validator module to ensure it correctly validates
manifest files against the schema.
"""
import json
import tempfile
from pathlib import Path

import pytest

from code.src.audit.manifest_schema_validator import (
    load_manifest,
    validate_manifest_schema,
    run_manifest_schema_validation,
)


class TestManifestSchemaValidation:
    """Test suite for manifest schema validation."""

    @pytest.fixture
    def valid_manifest(self):
        """Create a valid manifest dictionary."""
        return {
            "version": "1.0.0",
            "generated_at": "2024-01-15T10:30:00Z",
            "project_id": "PROJ-492",
            "artifacts": {
                "data/raw/test.html": "a" * 64,
                "output/audit_report.json": "b" * 64,
                "output/summary_report.csv": "c" * 64,
            },
            "metadata": {
                "python_version": "3.10.0",
                "platform": "linux",
                "seed": 42,
            },
        }

    @pytest.fixture
    def schema_path(self):
        """Return the path to the manifest schema."""
        return Path(__file__).parent.parent.parent / "contracts" / "manifest.schema.yaml"

    def test_load_manifest_valid_file(self, valid_manifest, tmp_path, schema_path):
        """Test loading a valid manifest file."""
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(valid_manifest, f)

        data, error = load_manifest(manifest_file)
        assert error is None
        assert data is not None
        assert data["version"] == "1.0.0"
        assert len(data["artifacts"]) == 3

    def test_load_manifest_file_not_found(self, tmp_path):
        """Test loading a non-existent manifest file."""
        non_existent = tmp_path / "does_not_exist.json"
        data, error = load_manifest(non_existent)
        assert data is None
        assert error is not None
        assert "not found" in error.lower()

    def test_load_manifest_invalid_json(self, tmp_path):
        """Test loading a manifest with invalid JSON."""
        manifest_file = tmp_path / "invalid.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json }")

        data, error = load_manifest(manifest_file)
        assert data is None
        assert error is not None
        assert "json" in error.lower()

    def test_validate_manifest_schema_valid(self, valid_manifest, schema_path):
        """Test validation of a valid manifest."""
        is_valid, errors = validate_manifest_schema(valid_manifest, schema_path)
        assert is_valid is True
        assert errors == []

    def test_validate_manifest_schema_missing_version(self, valid_manifest, schema_path):
        """Test validation fails when version is missing."""
        invalid_manifest = valid_manifest.copy()
        del invalid_manifest["version"]
        is_valid, errors = validate_manifest_schema(invalid_manifest, schema_path)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_manifest_schema_invalid_hash_format(self, valid_manifest, schema_path):
        """Test validation fails when hash is not 64 hex chars."""
        invalid_manifest = valid_manifest.copy()
        invalid_manifest["artifacts"] = {
            "test.txt": "invalid_hash"  # Not 64 hex chars
        }
        is_valid, errors = validate_manifest_schema(invalid_manifest, schema_path)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_manifest_schema_missing_artifacts(self, valid_manifest, schema_path):
        """Test validation fails when artifacts key is missing."""
        invalid_manifest = valid_manifest.copy()
        del invalid_manifest["artifacts"]
        is_valid, errors = validate_manifest_schema(invalid_manifest, schema_path)
        assert is_valid is False
        assert len(errors) > 0

    def test_run_manifest_schema_validation_success(self, valid_manifest, tmp_path, schema_path):
        """Test run function with valid manifest."""
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(valid_manifest, f)

        exit_code = run_manifest_schema_validation(manifest_file, schema_path)
        assert exit_code == 0

    def test_run_manifest_schema_validation_failure(self, tmp_path, schema_path):
        """Test run function with invalid manifest."""
        manifest_file = tmp_path / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump({"invalid": "data"}, f)

        exit_code = run_manifest_schema_validation(manifest_file, schema_path)
        assert exit_code == 1

    def test_schema_path_not_found(self, valid_manifest, tmp_path):
        """Test validation when schema file is missing."""
        non_existent_schema = tmp_path / "non_existent_schema.yaml"
        is_valid, errors = validate_manifest_schema(valid_manifest, non_existent_schema)
        assert is_valid is False
        assert len(errors) == 1
        assert "not found" in errors[0].lower()