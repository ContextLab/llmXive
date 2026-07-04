"""
Custom exceptions for the p-value validity assessment pipeline.
"""

class HighDimensionalInstabilityError(Exception):
    """
    Raised when a matrix exhibits numerical instability indicative of
    high-dimensional singular behavior (e.g., condition number > 10^12).

    This error signals that standard inversion or decomposition methods
    are unreliable without regularization.
    """
    def __init__(self, message: str, condition_number: float = None):
        super().__init__(message)
        self.condition_number = condition_number
