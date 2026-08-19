"""
Custom exceptions for the llmXive research pipeline.
"""
class DataQualityError(Exception):
    """Raised when data quality checks fail (e.g., match proportion < threshold)."""
    def __init__(self, message: str, match_proportion: float):
        super().__init__(message)
        self.match_proportion = match_proportion
        self.message = message

class GeocodingError(Exception):
    """Raised when geocoding or CRS transformation fails."""
    pass

class SpeciesFilterError(Exception):
    """Raised when species filtering logic encounters an error."""
    pass
