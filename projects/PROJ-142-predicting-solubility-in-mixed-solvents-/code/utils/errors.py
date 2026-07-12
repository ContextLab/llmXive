"""
errors.py: Custom exception classes for data and validation errors.
"""
from typing import Optional

class CustomDataError(Exception):
    """Base exception for custom data errors."""
    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

class MissingURLError(CustomDataError):
    """Raised when a required data URL is missing or inaccessible."""
    def __init__(self, url: str, message: str = "Data URL missing or inaccessible") -> None:
        super().__init__(f"{message}: {url}", details=url)

class InvalidStoichiometryError(CustomDataError):
    """Raised when composition values do not sum to 1.0 within tolerance."""
    def __init__(self, sum_value: float, tolerance: float = 1e-6) -> None:
        message = f"Composition sum {sum_value} is not within tolerance {tolerance} of 1.0"
        super().__init__(message, details=f"Sum: {sum_value}, Tolerance: {tolerance}")
