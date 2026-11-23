"""
Custom exceptions for the llmXive ball milling prediction pipeline.
"""

class DataIngestionError(Exception):
    """Raised when there is an error during data ingestion from external sources."""

    def __init__(self, message: str = "Data ingestion failed"):
        super().__init__(message)
        self.message = message


class MissingTimestampError(Exception):
    """Raised when a required timestamp is missing from the data."""

    def __init__(self, message: str = "Missing timestamp in data"):
        super().__init__(message)
        self.message = message


class GPRResourceLimitExceeded(Exception):
    """
    Raised when Gaussian Process Regression training exceeds configured
    resource limits (runtime or memory).
    """

    def __init__(self, runtime_seconds: float, memory_gb: float):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        message = (
            f"GPR training exceeded resource limits: "
            f"runtime {runtime_seconds:.2f}s, memory {memory_gb:.2f}GB"
        )
        super().__init__(message)


class InsufficientDataError(Exception):
    """Raised when the dataset does not meet minimum size requirements."""

    def __init__(self, message: str = "Insufficient data for processing"):
        super().__init__(message)
        self.message = message


class MissingDataError(Exception):
    """Raised when required data is missing or incomplete."""

    def __init__(self, message: str = "Required data is missing"):
        super().__init__(message)
        self.message = message


class StratificationError(Exception):
    """Raised when stratified splitting is not possible due to data constraints."""

    def __init__(self, message: str = "Stratification failed: insufficient unique values"):
        super().__init__(message)
        self.message = message


class SchemaValidationError(Exception):
    """Raised when data fails schema validation."""

    def __init__(self, message: str = "Schema validation failed"):
        super().__init__(message)
        self.message = message


class SourceConnectionError(Exception):
    """Raised when connection to a data source fails."""

    def __init__(self, message: str = "Failed to connect to data source"):
        super().__init__(message)
        self.message = message


class SourceAuthenticationError(Exception):
    """Raised when authentication to a data source fails."""

    def __init__(self, message: str = "Authentication failed for data source"):
        super().__init__(message)
        self.message = message


class SourceNotFoundError(Exception):
    """Raised when a requested data source or dataset is not found."""

    def __init__(self, message: str = "Data source or dataset not found"):
        super().__init__(message)
        self.message = message


class DataFormatError(Exception):
    """Raised when data format is invalid or unexpected."""

    def __init__(self, message: str = "Invalid data format"):
        super().__init__(message)
        self.message = message