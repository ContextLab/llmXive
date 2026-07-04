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
from code.src.utils.logger import get_default_logger


@pytest.fixture
def valid_manifest_data() -> Dict[str, Any]:
    """Fixture providing valid manifest data."""
    return {
        "version": "1.0.0",
        "generated_at": "2026-01-01T12:00:00Z",
        "project_id": "PROJ-492-evaluating-the-statistical-validity-of-p",
        "artifacts": [
            {
                "path": "output/audit_report.json",
                "hash": "a" * 64,
                "algorithm": "sha256",
                "size_bytes": 1024,
            }
        ],
    }

@pytest.fixture
def invalid_manifest_data_missing_version() -> Dict[str, Any]:
    """Fixture providing manifest data missing required 'version' field."""
    return {
        "generated_at": "2026-01-01T12:00:00Z",
        "artifacts": [
            {"path": "output/test.json", "hash": "a" * 64, "algorithm": "sha256"}
        ],
    }

@pytest.fixture
def invalid_manifest_data_bad_hash() -> Dict[str, Any]:
    """Fixture providing manifest data with invalid hash format."""
    return {
        "version": "1.0.0",
        "generated_at": "2026-01-01T12:00:00Z",
        "artifacts": [
            {"path": "output/test.json", "hash": "invalid-hash", "algorithm": "sha256"}
        ],
    }

@pytest.fixture
def valid_manifest_file(tmp_path: Path, valid_manifest_data: Dict[str, Any]) -> Path:
    """Fixture creating a valid manifest file."""
    manifest_path = tmp_path / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(valid_manifest_data, f)
    return manifest_path

@pytest.fixture
def invalid_manifest_file_missing_version(
    tmp_path: Path, invalid_manifest_data_missing_version: Dict[str, Any]
) -> Path:
    """Fixture creating an invalid manifest file (missing version)."""
    manifest_path = tmp_path / "manifest_invalid.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(invalid_manifest_data_missing_version, f)
    return manifest_path

@pytest.fixture
def schema_path(tmp_path: Path) -> Path:
    """Fixture returning the path to the manifest schema."""
    # Use the actual schema file in the project
    return Path("contracts/manifest.schema.yaml")

def test_load_manifest_success(valid_manifest_file: Path):
    """Test loading a valid manifest file."""
    data = load_manifest(valid_manifest_file)
    assert data is not None
    assert data["version"] == "1.0.0"
    assert len(data["artifacts"]) == 1

def test_load_manifest_file_not_found():
    """Test loading a non-existent manifest file."""
    data = load_manifest(Path("nonexistent/path/manifest.json"))
    assert data is None

def test_load_manifest_invalid_json(tmp_path: Path):
    """Test loading a file with invalid JSON."""
    invalid_path = tmp_path / "bad_manifest.json"
    with open(invalid_path, "w", encoding="utf-8") as f:
        f.write("{ invalid json }")
    
    data = load_manifest(invalid_path)
    assert data is None

def test_validate_manifest_schema_valid(valid_manifest_data: Dict[str, Any], schema_path: Path):
    """Test validation of valid manifest data."""
    is_valid, errors = validate_manifest_schema(valid_manifest_data, schema_path)
    assert is_valid is True
    assert len(errors) == 0

def test_validate_manifest_schema_missing_version(
    invalid_manifest_data_missing_version: Dict[str, Any], schema_path: Path
):
    """Test validation fails when required 'version' is missing."""
    is_valid, errors = validate_manifest_schema(invalid_manifest_data_missing_version, schema_path)
    assert is_valid is False
    assert len(errors) > 0
    # Check that an error about 'version' is present
    error_str = " ".join(errors)
    assert "version" in error_str.lower()

def test_validate_manifest_schema_bad_hash(
    invalid_manifest_data_bad_hash: Dict[str, Any], schema_path: Path
):
    """Test validation fails when hash format is invalid."""
    is_valid, errors = validate_manifest_schema(invalid_manifest_data_bad_hash, schema_path)
    assert is_valid is False
    assert len(errors) > 0
    error_str = " ".join(errors)
    assert "hash" in error_str.lower() or "pattern" in error_str.lower()

def test_run_manifest_schema_validation_success(valid_manifest_file: Path, schema_path: Path, caplog):
    """Test full validation run with a valid manifest."""
    # Temporarily patch the default paths for this test
    import code.src.audit.manifest_schema_validator as module
    original_manifest_path = module.MANIFEST_PATH
    original_schema_path = module.SCHEMA_PATH
    
    module.MANIFEST_PATH = valid_manifest_file
    module.SCHEMA_PATH = schema_path
    
    try:
        result = run_manifest_schema_validation()
        assert result is True
    finally:
        module.MANIFEST_PATH = original_manifest_path
        module.SCHEMA_PATH = original_schema_path

def test_run_manifest_schema_validation_failure(
    invalid_manifest_file_missing_version: Path, schema_path: Path
):
    """Test full validation run with an invalid manifest."""
    import code.src.audit.manifest_schema_validator as module
    original_manifest_path = module.MANIFEST_PATH
    original_schema_path = module.SCHEMA_PATH
    
    module.MANIFEST_PATH = invalid_manifest_file_missing_version
    module.SCHEMA_PATH = schema_path
    
    try:
        result = run_manifest_schema_validation()
        assert result is False
    finally:
        module.MANIFEST_PATH = original_manifest_path
        module.SCHEMA_PATH = original_schema_path