"""
Custom exceptions for data quality and geocoding errors.
"""
class DataQualityError(Exception):
    """Raised when data quality checks fail."""
    pass

class GeocodingError(Exception):
    """Raised when geocoding operations fail."""
    pass

class SpeciesFilterError(Exception):
    """Raised when species filtering criteria cannot be met."""
    pass
