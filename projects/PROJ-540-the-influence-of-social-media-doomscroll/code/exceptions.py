"""
Custom exceptions for the research pipeline.
"""

class PowerLimitationError(Exception):
    """Raised when statistical power is insufficient for the analysis."""
    pass

class MathematicalCouplingError(Exception):
    """Raised when mathematical coupling is detected between variables."""
    pass

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass