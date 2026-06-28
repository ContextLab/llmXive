"""Schema validation utilities for AB test audit data.

This module provides utilities to validate extracted A/B test summaries
and audit records against their respective JSON schemas defined in
contracts/extracted_summary.schema.yaml and contracts/audit_record.schema.yaml.

Functions:
    validate_ab_summary: Validate AB test summary data
    validate_audit_record: Validate audit record data
    get_ab_summary_validator: Get validator instance for AB summaries
    get_audit_record_validator: Get validator instance for audit records
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from jsonschema import Draft7Validator, ValidationError

# Schema file paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "contracts"
EXTRACTED_SUMMARY_SCHEMA_PATH = SCHEMAS_DIR / "extracted_summary.schema.yaml"
AUDIT_RECORD_SCHEMA_PATH = SCHEMAS_DIR / "audit_record.schema.yaml"


class SchemaValidator:
    """A validator that checks data against a JSON schema."""

    def __init__(self, schema_path: Path, schema_name: str):
        """Initialize the validator with a schema file.

        Args:
            schema_path: Path to the YAML schema file
            schema_name: Human-readable name for error messages
        """
        self.schema_path = schema_path
        self.schema_name = schema_name
        self._schema: Optional[Dict[str, Any]] = None
        self._validator: Optional[Draft7Validator] = None

    @property
    def schema(self) -> Dict[str, Any]:
        """Lazy-load the schema from disk."""
        if self._schema is None:
            if not self.schema_path.exists():
                raise FileNotFoundError(
                    f"Schema file not found: {self.schema_path}"
                )
            with open(self.schema_path, "r", encoding="utf-8") as f:
                self._schema = yaml.safe_load(f)
        return self._schema

    @property
    def validator(self) -> Draft7Validator:
        """Get the jsonschema validator instance."""
        if self._validator is None:
            self._validator = Draft7Validator(self.schema)
        return self._validator

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate data against the schema.

        Args:
            data: The data to validate

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = list(self.validator.iter_errors(data))
        if not errors:
            return True, []

        error_messages = []
        for error in errors:
            path = ".".join(map(str, error.path)) if error.path else "root"
            error_messages.append(
                f"[{self.schema_name}] {error.message} at {path}"
            )
        return False, error_messages


def _get_validator(schema_path: Path, schema_name: str) -> SchemaValidator:
    """Factory function to create a SchemaValidator instance."""
    return SchemaValidator(schema_path, schema_name)


def get_ab_summary_validator() -> SchemaValidator:
    """Get a validator for extracted AB test summaries.

    Returns:
        SchemaValidator configured for extracted_summary.schema.yaml
    """
    return _get_validator(EXTRACTED_SUMMARY_SCHEMA_PATH, "extracted_summary")


def get_audit_record_validator() -> SchemaValidator:
    """Get a validator for audit records.

    Returns:
        SchemaValidator configured for audit_record.schema.yaml
    """
    return _get_validator(AUDIT_RECORD_SCHEMA_PATH, "audit_record")


def validate_ab_summary(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate AB test summary data against the extracted_summary schema.

    Args:
        data: The AB test summary data to validate

    Returns:
        Tuple of (is_valid, list of error messages)

    Example:
        >>> is_valid, errors = validate_ab_summary({"url": "https://example.com"})
        >>> if is_valid:
        ...     print("Valid!")
        >>> else:
        ...     print(f"Errors: {errors}")
    """
    validator = get_ab_summary_validator()
    return validator.validate(data)


def validate_audit_record(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate audit record data against the audit_record schema.

    Args:
        data: The audit record data to validate

    Returns:
        Tuple of (is_valid, list of error messages)

    Example:
        >>> is_valid, errors = validate_audit_record({"summary_id": "123"})
        >>> if is_valid:
        ...     print("Valid!")
        >>> else:
        ...     print(f"Errors: {errors}")
    """
    validator = get_audit_record_validator()
    return validator.validate(data)
