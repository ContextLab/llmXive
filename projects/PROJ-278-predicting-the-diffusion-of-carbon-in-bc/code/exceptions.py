"""Custom exceptions for the carbon diffusion prediction pipeline."""

class DataInsufficientError(Exception):
    """Raised when data is missing, invalid, or insufficient for processing."""
    pass

class PowerWarning(Warning):
    """Warning raised when statistical power is low (e.g., sample size < 30)."""
    pass

class SHAPError(Exception):
    """Raised when SHAP value computation fails."""
    pass
