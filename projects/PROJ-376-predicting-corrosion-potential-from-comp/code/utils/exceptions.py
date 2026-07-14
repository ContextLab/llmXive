"""
Custom exceptions for the corrosion potential prediction pipeline.

This module defines specific exception classes used throughout the data
ingestion, validation, and modeling processes to provide clear error
handling and debugging information.
"""


class CorrosionPipelineError(Exception):
    """Base exception for all corrosion pipeline errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        base = self.message
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base} [{detail_str}]"
        return base


class DataInsufficientError(CorrosionPipelineError):
    """
    Raised when the dataset does not meet minimum requirements for analysis.

    This occurs when:
    - The number of records is below the minimum threshold (e.g., < 500).
    - Required fields are missing or null in critical columns.
    - The number of unique alloy designations is insufficient for GroupKFold.
    - External data sources are unreachable or return empty results.

    Attributes:
        message (str): Human-readable description of the insufficiency.
        details (dict): Optional context (e.g., record_count, missing_fields, threshold).
    """

    def __init__(
        self,
        message: str,
        record_count: int | None = None,
        threshold: int | None = None,
        missing_fields: list[str] | None = None,
        source: str | None = None,
    ):
        details = {}
        if record_count is not None:
            details["record_count"] = record_count
        if threshold is not None:
            details["threshold"] = threshold
        if missing_fields:
            details["missing_fields"] = missing_fields
        if source:
            details["source"] = source

        super().__init__(message, details)


class SchemaMismatchError(CorrosionPipelineError):
    """
    Raised when data fails schema validation or contract compliance.

    This occurs when:
    - A DataFrame column does not match the expected type or format.
    - Required columns defined in contracts are missing.
    - Enum values or constraints (e.g., pH range) are violated.
    - JSON/YAML configuration files fail structural validation.

    Attributes:
        message (str): Description of the mismatch.
        details (dict): Context including expected vs. actual values, field names, etc.
    """

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        expected_type: str | None = None,
        actual_type: str | None = None,
        missing_columns: list[str] | None = None,
        invalid_values: list[str] | None = None,
    ):
        details = {}
        if field_name:
            details["field"] = field_name
        if expected_type:
            details["expected_type"] = expected_type
        if actual_type:
            details["actual_type"] = actual_type
        if missing_columns:
            details["missing_columns"] = missing_columns
        if invalid_values:
            details["invalid_values"] = invalid_values

        super().__init__(message, details)
