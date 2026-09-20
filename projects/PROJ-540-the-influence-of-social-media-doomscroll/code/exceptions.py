"""
Custom exceptions for the Doomscrolling Anxiety study.
"""

class PowerLimitationError(Exception):
    """Raised when the sample size is insufficient for statistical power."""
    pass

class MathematicalCouplingError(Exception):
    """Raised when mathematical coupling or multicollinearity is detected."""
    pass

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass
