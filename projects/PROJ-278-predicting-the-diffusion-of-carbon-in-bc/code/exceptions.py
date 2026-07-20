"""
Custom exceptions and warnings for the Carbon Diffusion Prediction pipeline.

This module defines the core error handling infrastructure used across
the project to ensure deterministic behavior and clear failure modes.
"""

class DataInsufficientError(Exception):
    """
    Raised when the dataset does not meet the minimum sample size requirements
    for the chosen statistical method (e.g., < 30 samples for a standard split).

    This is a fatal error in strict mode, forcing the user to change parameters
    or acquire more data.
    """
    def __init__(self, message: str, required_samples: int = 30, actual_samples: int = 0):
        self.required_samples = required_samples
        self.actual_samples = actual_samples
        full_message = (
            f"{message} "
            f"(Required: {required_samples}, Actual: {actual_samples}). "
            f"Consider switching to LOOCV or acquiring more data."
        )
        super().__init__(full_message)


class PowerWarning(UserWarning):
    """
    Warning raised when the dataset size is small (e.g., < 30 samples),
    indicating that statistical power may be low for standard train/test splits.

    This warning triggers the fallback to Leave-One-Out Cross-Validation (LOOCV)
    in the training pipeline but allows execution to continue.
    """
    def __init__(self, message: str, sample_size: int = 0):
        self.sample_size = sample_size
        full_message = (
            f"{message} "
            f"(Sample size: {sample_size}). "
            f"Falling back to Leave-One-Out Cross-Validation (LOOCV) for robustness."
        )
        super().__init__(full_message)


class SHAPError(Exception):
    """
    Raised when SHAP value computation fails or produces invalid results.

    Unlike other errors, this does not fallback to alternative methods.
    The pipeline must halt to prevent reporting misleading feature importance.
    """
    def __init__(self, message: str, model_type: str = "Unknown"):
        self.model_type = model_type
        full_message = (
            f"SHAP computation failed for {model_type} model: {message}. "
            f"Execution halted as per FR-007 (no fallback allowed for SHAP)."
        )
        super().__init__(full_message)
