class TemporalVerificationError(Exception):
    """Raised when temporal separation in metadata cannot be verified."""
    pass

class DataUnavailableError(Exception):
    """Raised when required data is not available from the source."""
    pass
