from typing import Optional

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data is missing or unavailable."""
    def __init__(self, reason: str):
        super().__init__(f"Data unavailable: {reason}")

class InsufficientDataError(PipelineError):
    """Raised when there are insufficient subjects for analysis."""
    def __init__(self, count: int):
        super().__init__(f"Insufficient subjects (N={count}) for valid permutation test.")

class ConfigError(PipelineError):
    """Raised when configuration is invalid."""
    pass

class IntegrityError(PipelineError):
    """Raised when data integrity checks fail."""
    pass

def raise_data_unavailable(reason: str) -> DataUnavailableError:
    """Helper to raise DataUnavailableError."""
    raise DataUnavailableError(reason)

def raise_n_insufficient(count: int) -> InsufficientDataError:
    """Helper to raise InsufficientDataError."""
    raise InsufficientDataError(count)
