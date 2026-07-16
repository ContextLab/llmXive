"""
Custom exceptions for the llmXive ball milling research pipeline.

This module defines the hierarchy of errors used throughout the data ingestion,
preprocessing, and modeling stages to ensure consistent error handling and logging.
"""

class DataIngestionError(Exception):
    """
    Base exception for all data ingestion failures.
    
    Attributes:
        message (str): Human-readable error message.
        source (str): The data source where the error occurred (e.g., 'materials_project', 'nist').
    """
    def __init__(self, message: str, source: str = "unknown"):
        self.message = message
        self.source = source
        super().__init__(f"[{source}] {message}")

class SourceConnectionError(DataIngestionError):
    """
    Raised when a connection to a data source cannot be established.
    
    Attributes:
        message (str): Error description.
        source (str): The unreachable data source.
        status_code (int, optional): HTTP status code if applicable.
    """
    def __init__(self, message: str, source: str, status_code: int = None):
        self.status_code = status_code
        suffix = f" (Status: {status_code})" if status_code else ""
        super().__init__(f"{message}{suffix}", source)

class SourceAuthenticationError(DataIngestionError):
    """
    Raised when API authentication fails for a data source.
    
    Attributes:
        message (str): Error description.
        source (str): The data source requiring authentication.
    """
    def __init__(self, message: str, source: str):
        super().__init__(f"Authentication failed: {message}", source)

class SourceNotFoundError(DataIngestionError):
    """
    Raised when a specific dataset or resource is not found on the source.
    
    Attributes:
        message (str): Error description.
        source (str): The data source.
        resource_id (str): The specific ID or key that was not found.
    """
    def __init__(self, message: str, source: str, resource_id: str = None):
        self.resource_id = resource_id
        id_suffix = f" (Resource ID: {resource_id})" if resource_id else ""
        super().__init__(f"{message}{id_suffix}", source)

class DataFormatError(DataIngestionError):
    """
    Raised when the data retrieved from a source cannot be parsed or is malformed.
    
    Attributes:
        message (str): Error description.
        source (str): The data source.
        expected_format (str): The expected format (e.g., 'JSON', 'CSV').
        actual_format (str, optional): The actual format detected.
    """
    def __init__(self, message: str, source: str, expected_format: str = None, actual_format: str = None):
        self.expected_format = expected_format
        self.actual_format = actual_format
        suffix = ""
        if expected_format and actual_format:
            suffix = f" (Expected: {expected_format}, Got: {actual_format})"
        super().__init__(f"{message}{suffix}", source)

class SchemaValidationError(DataIngestionError):
    """
    Raised when data fails validation against the defined dataset schema.
    
    Attributes:
        message (str): Error description.
        source (str): The data source.
        missing_fields (list[str]): List of fields missing from the data.
    """
    def __init__(self, message: str, source: str, missing_fields: list = None):
        self.missing_fields = missing_fields or []
        fields_suffix = f" (Missing: {', '.join(self.missing_fields)})" if self.missing_fields else ""
        super().__init__(f"{message}{fields_suffix}", source)

class InsufficientDataError(DataIngestionError):
    """
    Raised when the aggregated dataset does not meet the minimum row count requirements.
    
    Attributes:
        message (str): Error description.
        required_count (int): The minimum required number of rows.
        actual_count (int): The actual number of rows found.
    """
    def __init__(self, message: str, required_count: int, actual_count: int):
        self.required_count = required_count
        self.actual_count = actual_count
        super().__init__(f"{message} (Required: {required_count}, Found: {actual_count})", "pipeline")

class GPRResourceLimitExceeded(Exception):
    """
    Raised when Gaussian Process Regression training exceeds resource limits.
    
    This exception is caught by the training CLI to trigger the fallback to Random Forest.
    
    Attributes:
        runtime_seconds (float): Duration of the training attempt in seconds.
        memory_gb (float): Peak memory usage in gigabytes.
    """
    def __init__(self, runtime_seconds: float, memory_gb: float):
        self.runtime_seconds = runtime_seconds
        self.memory_gb = memory_gb
        msg = (
            f"GPR training exceeded resource limits. "
            f"Runtime: {runtime_seconds:.2f}s (limit: 1800s), "
            f"Memory: {memory_gb:.2f}GB (limit: 5.0GB). "
            f"Triggering fallback to Random Forest."
        )
        super().__init__(msg)
