"""
Custom exceptions for the doomscrolling anxiety analysis pipeline.
"""

class PowerLimitationError(Exception):
    """Raised when the sample size is below the required power threshold."""
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
