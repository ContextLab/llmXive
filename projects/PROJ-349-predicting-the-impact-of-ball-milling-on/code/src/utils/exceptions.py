"""
Custom exception classes for the ball milling PSD prediction pipeline.

These exceptions are used to handle specific error conditions during
data ingestion, validation, and model training processes.
"""

class DataIngestionError(Exception):
    """
    Raised when an error occurs during data ingestion from external sources.

    Attributes:
        message (str): Human-readable error message.
        source (str): The data source that failed (e.g., 'Materials Project', 'NIST').
    """
    def __init__(self, message: str, source: str = "Unknown"):
        self.message = message
        self.source = source
        super().__init__(f"[DataIngestionError] Source '{source}': {message}")


class MissingTimestampError(Exception):
    """
    Raised when required timestamp data is missing and cannot be imputed.

    Attributes:
        message (str): Human-readable error message.
        field (str): The specific field missing timestamps.
    """
    def __init__(self, message: str, field: str = "timestamp"):
        self.message = message
        self.field = field
        super().__init__(f"[MissingTimestampError] Field '{field}': {message}")


class GPRResourceLimitExceeded(Exception):
    """
    Raised when Gaussian Process Regression training exceeds resource limits.

    Attributes:
        runtime_seconds (float): The runtime that was exceeded.
        memory_gb (float): The memory usage that was exceeded.
        limit_type (str): Either 'runtime' or 'memory'.
    """
    def __init__(self, runtime_seconds: float = 0.0, memory_gb: float = 0.0):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb

        if runtime_seconds > 0 and memory_gb > 0:
            self.limit_type = "both"
            self.message = f"Exceeded both runtime ({runtime_seconds:.1f}s) and memory ({memory_gb:.2f}GB) limits."
        elif runtime_seconds > 0:
            self.limit_type = "runtime"
            self.message = f"Exceeded runtime limit: {runtime_seconds:.1f} seconds."
        elif memory_gb > 0:
            self.limit_type = "memory"
            self.message = f"Exceeded memory limit: {memory_gb:.2f} GB."
        else:
            self.limit_type = "unknown"
            self.message = "Resource limits exceeded (details unknown)."

        super().__init__(f"[GPRResourceLimitExceeded] {self.message}")


class InsufficientDataError(Exception):
    """
    Raised when the dataset does not meet minimum size requirements.

    Attributes:
        message (str): Human-readable error message.
        required_rows (int): The minimum number of rows required.
        actual_rows (int): The actual number of rows found.
    """
    def __init__(self, message: str, required_rows: int = 0, actual_rows: int = 0):
        self.required_rows = required_rows
        self.actual_rows = actual_rows
        self.message = message
        super().__init__(f"[InsufficientDataError] {message} (Required: {required_rows}, Found: {actual_rows})")


class SchemaValidationError(Exception):
    """
    Raised when data validation against the schema fails.

    Attributes:
        message (str): Human-readable error message.
        errors (list): List of specific validation errors.
    """
    def __init__(self, message: str, errors: list = None):
        self.message = message
        self.errors = errors or []
        error_details = "; ".join(self.errors) if self.errors else ""
        full_msg = f"{message}"
        if error_details:
            full_msg += f": {error_details}"
        super().__init__(f"[SchemaValidationError] {full_msg}")