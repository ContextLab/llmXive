"""
Data loading module.

Enforces "fail loud" policy: raises DataUnavailableError immediately if
required data (human_intensity_score) is missing. No synthetic fallbacks.
"""

class DataUnavailableError(Exception):
    """Raised when required data is unavailable or missing critical fields."""
    pass
