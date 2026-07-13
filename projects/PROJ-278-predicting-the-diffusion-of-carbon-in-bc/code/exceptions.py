class DataInsufficientError(Exception):
    """Raised when the dataset is too small for the requested operation."""
    pass

class PowerWarning(Warning):
    """Warning raised when statistical power is low (e.g., small sample size)."""
    pass

class SHAPError(Exception):
    """Raised when SHAP value computation fails."""
    pass
