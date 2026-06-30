"""
Contract test for dataset schema validation (T019).

Validates that dataset artifacts conform to the schema defined in
contracts/dataset.schema.yaml.

Expected schema fields (per T010):
  - name (string)
  - url (string)
  - variables (list)
  - size_mb (number)
  - checksum (string, sha256)
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
DATA_DIR = PROJECT_ROOT / "data"

# Required fields per T010
REQUIRED_FIELDS = ["name", "url", "variables", "size_mb", "checksum"]
OPTIONAL_FIELDS = ["description", "created_at", "updated_at"]

def load_schema() -> Dict[str, Any]:
    """Load the dataset schema contract."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_field_types(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate that each field in the record matches the expected type in the schema.
    Returns a list of error messages.
    """
    errors = []
    properties = schema.get("properties", {})

    for field_name, value in record.items():
        if field_name not in properties:
            # Allow extra fields if schema allows additionalProperties, otherwise error
            if not schema.get("additionalProperties", True):
                errors.append(f"Unexpected field: '{field_name}'")
            continue

        expected_type = properties[field_name].get("type")
        
        if expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Field '{field_name}' must be string, got {type(value).__name__}")
        elif expected_type == "number":
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' must be number, got {type(value).__name__}")
        elif expected_type == "integer":
            if not isinstance(value, int):
                errors.append(f"Field '{field_name}' must be integer, got {type(value).__name__}")
        elif expected_type == "array":
            if not isinstance(value, list):
                errors.append(f"Field '{field_name}' must be array, got {type(value).__name__}")
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                errors.append(f"Field '{field_name}' must be boolean, got {type(value).__name__}")
        elif expected_type == "object":
            if not isinstance(value, dict):
                errors.append(f"Field '{field_name}' must be object, got {type(value).__name__}")

    return errors

def validate_required_fields(record: Dict[str, Any]) -> List[str]:
    """Check that all required fields are present."""
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    return [f"Missing required field: '{f}'" for f in missing]

def validate_checksum_format(checksum: str) -> List[str]:
    """Validate that checksum is a valid sha256 hex string."""
    if not isinstance(checksum, str):
        return ["'checksum' must be a string"]
    if len(checksum) != 64:
        return [f"'checksum' must be 64 characters (sha256), got {len(checksum)}"]
    try:
        int(checksum, 16)
    except ValueError:
        return ["'checksum' must be a valid hexadecimal string"]
    return []

def validate_variable_list(variables: Any) -> List[str]:
    """Validate that 'variables' is a non-empty list of strings."""
    if not isinstance(variables, list):
        return ["'variables' must be a list"]
    if len(variables) == 0:
        return ["'variables' list cannot be empty"]
    non_strings = [v for v in variables if not isinstance(v, str)]
    if non_strings:
        return [f"All items in 'variables' must be strings, found non-strings: {non_strings}"]
    return []

def validate_dataset_record(record: Dict[str, Any]) -> List[str]:
    """
    Perform full validation of a dataset record against the schema.
    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # 1. Check required fields
    errors.extend(validate_required_fields(record))
    if errors:
        return errors  # Fail fast if missing required fields

    # 2. Load schema and check types
    try:
        schema = load_schema()
    except FileNotFoundError as e:
        return [str(e)]

    errors.extend(validate_field_types(record, schema))

    # 3. Specific business logic validations
    errors.extend(validate_checksum_format(record["checksum"]))
    errors.extend(validate_variable_list(record["variables"]))

    return errors

class TestDatasetSchema:
    """Contract tests for dataset schema validation."""

    @pytest.fixture
    def valid_record(self) -> Dict[str, Any]:
        """Create a valid dataset record for testing."""
        return {
            "name": "UCI_HAR",
            "url": "https://huggingface.co/datasets/UCI_HAR",
            "variables": ["accelerometer_x", "accelerometer_y", "gyroscope_z", "activity_label"],
            "size_mb": 2.5,
            "checksum": "a" * 64  # Valid hex string
        }

    @pytest.fixture
    def schema(self) -> Dict[str, Any]:
        """Load the schema."""
        return load_schema()

    def test_schema_exists(self):
        """Verify the schema contract file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

    def test_required_fields_present(self, valid_record):
        """Verify all required fields are present in a valid record."""
        errors = validate_required_fields(valid_record)
        assert len(errors) == 0, f"Missing required fields: {errors}"

    def test_type_validation_strings(self, valid_record):
        """Verify string fields are validated correctly."""
        valid_record["name"] = 123  # Invalid
        errors = validate_field_types(valid_record, load_schema())
        assert any("must be string" in e for e in errors)

    def test_type_validation_list(self, valid_record):
        """Verify list fields are validated correctly."""
        valid_record["variables"] = "not a list"  # Invalid
        errors = validate_field_types(valid_record, load_schema())
        assert any("must be array" in e for e in errors)

    def test_type_validation_number(self, valid_record):
        """Verify number fields are validated correctly."""
        valid_record["size_mb"] = "2.5"  # Invalid (string instead of number)
        errors = validate_field_types(valid_record, load_schema())
        assert any("must be number" in e for e in errors)

    def test_checksum_format_valid(self, valid_record):
        """Verify valid checksum format passes."""
        errors = validate_checksum_format(valid_record["checksum"])
        assert len(errors) == 0

    def test_checksum_format_invalid_length(self, valid_record):
        """Verify checksum with wrong length fails."""
        errors = validate_checksum_format("short")
        assert len(errors) > 0

    def test_checksum_format_invalid_hex(self, valid_record):
        """Verify checksum with non-hex characters fails."""
        errors = validate_checksum_format("z" * 64)
        assert len(errors) > 0

    def test_variables_empty_list(self, valid_record):
        """Verify empty variables list fails."""
        valid_record["variables"] = []
        errors = validate_variable_list(valid_record["variables"])
        assert len(errors) > 0

    def test_variables_non_string_items(self, valid_record):
        """Verify variables with non-string items fails."""
        valid_record["variables"] = ["valid", 123, None]
        errors = validate_variable_list(valid_record["variables"])
        assert len(errors) > 0

    def test_full_validation_passes(self, valid_record):
        """Verify a complete valid record passes all checks."""
        errors = validate_dataset_record(valid_record)
        assert len(errors) == 0, f"Validation failed: {errors}"

    def test_full_validation_missing_field(self, valid_record):
        """Verify missing required field fails full validation."""
        del valid_record["checksum"]
        errors = validate_dataset_record(valid_record)
        assert any("Missing required field" in e for e in errors)

    def test_full_validation_bad_checksum(self, valid_record):
        """Verify bad checksum fails full validation."""
        valid_record["checksum"] = "invalid"
        errors = validate_dataset_record(valid_record)
        assert any("checksum" in e.lower() for e in errors)

    def test_real_artifact_validation(self):
        """
        Test validation against actual dataset artifacts in data/ if they exist.
        This ensures the contract holds for real data.
        """
        if not DATA_DIR.exists():
            pytest.skip("Data directory not found, skipping real artifact test")

        # Look for JSON/YAML dataset manifests
        manifest_files = list(DATA_DIR.glob("*.json")) + list(DATA_DIR.glob("*.yaml"))
        
        if not manifest_files:
            pytest.skip("No dataset manifest files found in data/, skipping real artifact test")

        for manifest_path in manifest_files:
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    if manifest_path.suffix == ".json":
                        record = json.load(f)
                    else:
                        record = yaml.safe_load(f)
                
                errors = validate_dataset_record(record)
                # If errors exist, fail the test with details
                assert len(errors) == 0, f"Validation failed for {manifest_path.name}: {errors}"
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                pytest.fail(f"Could not parse manifest {manifest_path.name}: {e}")
            except FileNotFoundError:
                pytest.skip(f"Manifest file {manifest_path.name} disappeared during test")