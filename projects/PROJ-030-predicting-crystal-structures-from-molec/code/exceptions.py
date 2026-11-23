"""
Custom Exception Definitions for the Crystal Structure Prediction Pipeline.
"""
from typing import Any, Optional

class DownloadError(Exception):
    """Raised when a data download fails."""
    pass

class MemoryErrorHandled(Exception):
    """Raised when a memory error is caught and handled explicitly."""
    pass

class ValidationError(Exception):
    """Raised when data validation fails."""
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)

class CitationVerificationError(Exception):
    """Raised when dataset citation verification fails."""
    pass

class SourceUnreachableError(Exception):
    """Raised when the data source is unreachable."""
    pass
