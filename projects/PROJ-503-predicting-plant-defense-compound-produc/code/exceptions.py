"""
Custom exceptions for the plant defense prediction pipeline.

Defines error codes and exception classes for various failure modes:
- E_DATASET: Data acquisition failures
- E_PAIRING: Sample pairing failures
- E_TIMEOUT: Runtime timeout failures
- E_POWER: Power analysis failures
"""

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class E_DATASET(PipelineError):
    """Exception raised when dataset acquisition fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="E-DATASET", details=details)

class E_PAIRING(PipelineError):
    """Exception raised when sample pairing fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="E-PAIRING", details=details)

class E_TIMEOUT(PipelineError):
    """Exception raised when runtime timeout is exceeded."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="E-TIMEOUT", details=details)

class E_POWER(PipelineError):
    """Exception raised when power analysis fails (insufficient sample size)."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, code="E-POWER", details=details)
