from typing import Optional, Dict, Any

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

class ConfigurationError(PipelineError):
    """Error related to configuration issues."""
    pass

class ValidationError(PipelineError):
    """Error related to data validation failures."""
    pass

class DataInsufficientError(PipelineError):
    """Error raised when data is missing or insufficient for processing."""
    pass
