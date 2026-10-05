"""
Custom exception classes for the pipeline.
"""
from typing import Any, Optional

class DownloadError(Exception):
    """Raised when a data download fails."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class MemoryErrorHandled(Exception):
    """Raised when a memory error is caught and handled explicitly."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ValidationError(Exception):
    """Raised when data validation fails."""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(f"{message} (Field: {field}, Value: {value})")
