"""
Custom exceptions for the ball milling impact prediction pipeline.

This module defines specific exception classes used throughout the data
ingestion, preprocessing, and modeling stages to ensure consistent
error handling and clear communication of failure modes.
"""

class DataIngestionError(Exception):
    """
    Raised when an error occurs during data ingestion from any source.

    Attributes:
        message (str): Human-readable error message.
        source (str, optional): The name of the source that failed.
    """
    def __init__(self, message: str, source: str = None):
        self.message = message
        self.source = source
        if source:
            super().__init__(f"[Source: {source}] {message}")
        else:
            super().__init__(message)


class MissingTimestampError(Exception):
    """
    Raised when a required timestamp field is missing or invalid in the data.

    Attributes:
        message (str): Human-readable error message.
        field_name (str): The name of the missing/invalid timestamp field.
    """
    def __init__(self, message: str, field_name: str = None):
        self.message = message
        self.field_name = field_name
        if field_name:
            super().__init__(f"[Field: {field_name}] {message}")
        else:
            super().__init__(message)


class GPRResourceLimitExceeded(Exception):
    """
    Raised when Gaussian Process Regression training exceeds configured
    resource limits (runtime or memory).

    Attributes:
        message (str): Human-readable error message.
        runtime_seconds (float): The runtime in seconds when the limit was hit.
        memory_gb (float): The memory usage in GB when the limit was hit.
    """
    def __init__(self, runtime_seconds: float = None, memory_gb: float = None):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        parts = []
        if runtime_seconds is not None:
            parts.append(f"Runtime: {runtime_seconds:.2f}s")
        if memory_gb is not None:
            parts.append(f"Memory: {memory_gb:.2f}GB")
        details = ", ".join(parts) if parts else "Resource limit exceeded"
        super().__init__(f"GPR training aborted due to resource limits: {details}")


class InsufficientDataError(Exception):
    """
    Raised when the dataset does not meet minimum size or quality requirements.

    Attributes:
        message (str): Human-readable error message.
        required_count (int, optional): The minimum required number of rows.
        actual_count (int, optional): The actual number of rows found.
    """
    def __init__(self, message: str, required_count: int = None, actual_count: int = None):
        self.message = message
        self.required_count = required_count
        self.actual_count = actual_count
        if required_count is not None and actual_count is not None:
            super().__init__(f"{message} (Required: {required_count}, Found: {actual_count})")
        else:
            super().__init__(message)


class MissingDataError(Exception):
    """
    Raised when specific required data fields or columns are missing.

    Attributes:
        message (str): Human-readable error message.
        missing_fields (list): List of missing field names.
    """
    def __init__(self, message: str, missing_fields: list = None):
        self.message = message
        self.missing_fields = missing_fields
        if missing_fields:
            super().__init__(f"{message}: {', '.join(missing_fields)}")
        else:
            super().__init__(message)


class StratificationError(Exception):
    """
    Raised when stratified splitting fails due to insufficient unique values
    in the target variable.

    Attributes:
        message (str): Human-readable error message.
        target_column (str): The column that failed stratification.
        unique_values (int): The number of unique values found.
    """
    def __init__(self, message: str, target_column: str = None, unique_values: int = None):
        self.message = message
        self.target_column = target_column
        self.unique_values = unique_values
        if target_column and unique_values:
            super().__init__(f"{message} (Column: {target_column}, Unique values: {unique_values})")
        else:
            super().__init__(message)


class SchemaValidationError(Exception):
    """
    Raised when data fails schema validation checks.

    Attributes:
        message (str): Human-readable error message.
        violations (list): List of specific validation violations.
    """
    def __init__(self, message: str, violations: list = None):
        self.message = message
        self.violations = violations
        if violations:
            details = "; ".join(violations)
            super().__init__(f"{message}: {details}")
        else:
            super().__init__(message)