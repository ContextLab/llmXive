class CriticalValidationError(Exception):
    """Raised when all datasets fail validation checks (e.g., minimum sample size)."""
    pass

class EdgeCaseError(Exception):
    """Raised when a dataset or simulation encounters an edge case that cannot be handled."""
    pass
