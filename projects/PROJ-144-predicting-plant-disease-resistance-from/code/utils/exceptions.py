class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class DataAvailabilityError(Exception):
    """Raised when required data is not available."""
    pass

class TemporalVerificationWarning(Warning):
    """Warning for ambiguous temporal metadata."""
    pass

class TemporalVerificationError(Exception):
    """Error for critical temporal metadata failures."""
    pass

class ClassImbalanceError(Exception):
    """
    Raised when a stratified split results in a hold-out set (or CV fold)
    containing zero samples of the minority class.
    """
    pass

class ConvergenceWarning(Warning):
    """Warning when batch correction fails to converge."""
    pass

class DataQualityError(Exception):
    """Raised when data quality (e.g., InChIKey alignment) is insufficient."""
    pass
