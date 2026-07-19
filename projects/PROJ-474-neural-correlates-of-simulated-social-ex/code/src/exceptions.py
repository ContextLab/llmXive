from typing import Optional

class PipelineError(Exception):
    """Base class for pipeline errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when data is unavailable."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Data unavailable: {reason}")

class InsufficientDataError(PipelineError):
    """Raised when there's insufficient data."""
    def __init__(self, count: int):
        self.count = count
        super().__init__(f"Insufficient subjects (N={count}) for valid permutation test.")

class ConfigError(PipelineError):
    """Raised when there is an error with the configuration file."""
    pass

class IntegrityError(PipelineError):
  """Raised when data integrity check fails"""
  pass


def raise_data_unavailable(reason: str) -> None:
    raise DataUnavailableError(reason)

def raise_n_insufficient(count: int) -> None:
    raise InsufficientDataError(count)