class TemporalVerificationError(Exception):
    """Raised when temporal consistency checks fail."""
    pass

class DataUnavailableError(Exception):
    """Raised when required data is missing or unavailable."""
    pass