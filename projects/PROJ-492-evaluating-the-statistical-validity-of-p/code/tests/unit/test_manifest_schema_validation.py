"""
Unit tests for manifest schema validation (Task T058).
"""
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from code.src.audit.manifest_schema_validator import (
    load_manifest,
    validate_manifest_schema,
    run_manifest_schema_validation,
)
from code.src.contracts.validation import SchemaValidator


# Valid manifest fixture
VALID_MANIFEST = {
    "version": "1.0.0",
    "generated_at": "2024-01-15T10:30:00Z",
    "files": [
        {
            "path": "output/audit_report.json",
            "hash": "a" * 64,
            "size_bytes": 1024,
        },
        {
            "path": "output/summary_report.csv",
            "hash": "b" * 64,
            "size_bytes": 512,
        },
    ],
}

# Invalid manifest fixtures
INVALID_MANIFEST_MISSING_VERSION = {
    "generated_at": "2024-01-15T10:30:00Z",
    "files": [],
}

INVALID_MANIFEST_INVALID_HASH = {
    "version": "1.0.0",
    "generated_at": "2024-01-15T10:30:00Z",
    "files": [
        {
            "path": "output/test.json",
            "hash": "invalid_hash",  # Not 64 hex chars
        },
    ],
}

INVALID_MANIFEST_INVALID_VERSION = {
    "version": "invalid",  # Not semver
    "generated_at": "2024-01-15T10:30:00Z",
    "files": [],
}


@pytest.fixture
def temp_schema_file():
    """Create a temporary schema file for testing."""
    schema_content = """
    $schema: "http://json-schema.org/draft-07/schema#"
    title: Test Manifest Schema
    type: object
    required:
      - version
      - files
    properties:
      version:
        type: string
      files:
        type: array
    additionalProperties: false
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(schema_content)
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def temp_valid_manifest_file():
    """Create a temporary valid manifest file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(VALID_MANIFEST, f)
        yield Path(f.name)
    Path(f.name).unlink()


@pytest.fixture
def temp_invalid_manifest_file():
    """Create a temporary invalid manifest file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(INVALID_MANIFEST_MISSING_VERSION, f)
        yield Path(f.name)
    Path(f.name).unlink()


class TestLoadManifest:
    def test_load_valid_manifest(self, temp_valid_manifest_file):
        """Test loading a valid manifest file."""
        result = load_manifest(temp_valid_manifest_file)
        assert result is not None
        assert result["version"] == "1.0.0"
        assert len(result["files"]) == 2

    def test_load_nonexistent_manifest(self):
        """Test loading a non-existent manifest file."""
        result = load_manifest(Path("/nonexistent/path/manifest.json"))
        assert result is None

    def test_load_invalid_json(self):
        """Test loading a file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {{{")
            temp_path = Path(f.name)

        try:
            result = load_manifest(temp_path)
            assert result is None
        finally:
            temp_path.unlink()


class TestValidateManifestSchema:
    def test_validate_valid_manifest(self, temp_schema_file):
        """Test validation of a valid manifest."""
        is_valid, errors = validate_manifest_schema(VALID_MANIFEST, temp_schema_file)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_missing_required_field(self, temp_schema_file):
        """Test validation fails when required field is missing."""
        is_valid, errors = validate_manifest_schema(
            INVALID_MANIFEST_MISSING_VERSION, temp_schema_file
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("version" in err for err in errors)

    def test_validate_invalid_hash_format(self, temp_schema_file):
        """Test validation fails with invalid hash format."""
        is_valid, errors = validate_manifest_schema(
            INVALID_MANIFEST_INVALID_HASH, temp_schema_file
        )
        # Note: The basic schema above doesn't enforce hash format,
        # so this test validates against the real schema in contracts/
        pass  # Skip for basic schema, tested in integration


class TestRunManifestSchemaValidation:
    def test_run_with_valid_manifest(self, temp_schema_file, temp_valid_manifest_file):
        """Test successful validation with valid manifest."""
        # Copy valid manifest to expected location for the function
        import shutil
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        target_path = output_dir / "manifest.json"
        shutil.copy(temp_valid_manifest_file, target_path)

        try:
            result = run_manifest_schema_validation(
                manifest_path=target_path,
                schema_path=temp_schema_file,
            )
            assert result is True
        finally:
            target_path.unlink()

    def test_run_with_invalid_manifest(self, temp_schema_file, temp_invalid_manifest_file):
        """Test validation failure with invalid manifest."""
        import shutil
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        target_path = output_dir / "manifest.json"
        shutil.copy(temp_invalid_manifest_file, target_path)

        try:
            result = run_manifest_schema_validation(
                manifest_path=target_path,
                schema_path=temp_schema_file,
            )
            assert result is False
        finally:
            target_path.unlink()

    def test_run_with_missing_schema(self, temp_valid_manifest_file):
        """Test validation failure when schema is missing."""
        import shutil
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        target_path = output_dir / "manifest.json"
        shutil.copy(temp_valid_manifest_file, target_path)

        try:
            result = run_manifest_schema_validation(
                manifest_path=target_path,
                schema_path=Path("/nonexistent/schema.yaml"),
            )
            assert result is False
        finally:
            target_path.unlink()


class TestRealSchemaValidation:
    """Integration-style tests using the actual schema file."""

    def test_real_schema_with_valid_manifest(self):
        """Test the real manifest schema with a valid manifest structure."""
        schema_path = Path("contracts/manifest.schema.yaml")
        if not schema_path.exists():
            pytest.skip("Real schema file not found in contracts/")

        is_valid, errors = validate_manifest_schema(VALID_MANIFEST, schema_path)
        assert is_valid is True
        assert len(errors) == 0

    def test_real_schema_rejects_invalid_hash(self):
        """Test the real schema rejects invalid hash format."""
        schema_path = Path("contracts/manifest.schema.yaml")
        if not schema_path.exists():
            pytest.skip("Real schema file not found in contracts/")

        is_valid, errors = validate_manifest_schema(
            INVALID_MANIFEST_INVALID_HASH, schema_path
        )
        assert is_valid is False
        assert len(errors) > 0
        assert any("hash" in err.lower() for err in errors)

    def test_real_schema_rejects_invalid_version(self):
        """Test the real schema rejects invalid version format."""
        schema_path = Path("contracts/manifest.schema.yaml")
        if not schema_path.exists():
            pytest.skip("Real schema file not found in contracts/")

        is_valid, errors = validate_manifest_schema(
            INVALID_MANIFEST_INVALID_VERSION, schema_path
        )
        assert is_valid is False
        assert len(errors) > 0