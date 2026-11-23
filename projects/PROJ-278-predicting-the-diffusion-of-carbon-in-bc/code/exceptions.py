"""Custom exceptions for the project."""
class DataInsufficientError(Exception):
    """Raised when data is missing, insufficient, or invalid."""
    pass

class PowerWarning(Exception):
    """Raised when sample size is too low for robust statistical power."""
    pass

class SHAPError(Exception):
    """Raised when SHAP computation fails."""
    pass
