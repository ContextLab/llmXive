"""
Custom exceptions for the research pipeline.
Task T008: Configure error handling infrastructure.
"""

class DataQualityError(Exception):
    """Raised when data quality checks fail."""
    pass

class GeocodingError(Exception):
    """Raised when geocoding operations fail."""
    pass

class SpeciesFilterError(Exception):
    """Raised when species filtering logic fails."""
    pass
