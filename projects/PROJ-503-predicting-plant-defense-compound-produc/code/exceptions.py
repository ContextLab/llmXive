"""
Custom exception classes for the pipeline.
Defines specific error codes for different failure modes.
"""
import sys
from typing import Optional, Dict, Any

class PipelineError(Exception):
    """Base class for all pipeline errors."""
    def __init__(self, message: str, code: str = "E-UNKNOWN", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}
        self.message = message

class E_DATASET(PipelineError):
    """Error raised when dataset verification fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="E-DATASET", details=details)

class E_PAIRING(PipelineError):
    """Error raised when data pairing fails to meet thresholds."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="E-PAIRING", details=details)

class E_TIMEOUT(PipelineError):
    """Error raised when execution exceeds time limits."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="E-TIMEOUT", details=details)

class E_POWER(PipelineError):
    """Error raised when power analysis indicates insufficient sample size."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="E-POWER", details=details)
