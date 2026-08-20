class PowerLimitationError(Exception):
    """Raised when sample size is insufficient for statistical power."""
    pass

class MathematicalCouplingError(Exception):
    """Raised when variables are mathematically coupled (e.g., identical or derived from each other)."""
    pass

class DataValidationError(Exception):
    """Raised when data validation fails (schema, types, etc.)."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass
