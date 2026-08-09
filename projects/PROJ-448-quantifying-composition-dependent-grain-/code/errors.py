"""
Custom exception definitions for the llmXive research pipeline.

This module centralizes all custom exceptions used across the project
to ensure consistent error handling and reporting.
"""

class LlmXiveError(Exception):
    """Base exception for all llmXive project errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        
    def __str__(self):
        base = super().__str__()
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base} [{details_str}]"
        return base

class DataLoadError(LlmXiveError):
    """Raised when data loading or fetching fails."""
    pass

class ConfigurationError(LlmXiveError):
    """Raised when configuration validation or loading fails."""
    pass

class SurrogateModelError(LlmXiveError):
    """Raised when surrogate model computation or convergence fails."""
    pass

class ValidationError(LlmXiveError):
    """Raised when data or result validation checks fail."""
    pass

class ManifestError(LlmXiveError):
    """Raised when data manifest validation or generation fails."""
    pass

class ThermodynamicError(LlmXiveError):
    """Raised when thermodynamic calculations fail."""
    pass

class ExperimentalDataError(LlmXiveError):
    """Raised when experimental data fetching or processing fails."""
    pass

__all__ = [
    "LlmXiveError",
    "DataLoadError",
    "ConfigurationError",
    "SurrogateModelError",
    "ValidationError",
    "ManifestError",
    "ThermodynamicError",
    "ExperimentalDataError"
]