"""
Custom exceptions for the llmXive project.
"""

class DATA_INTEGRITY_ERROR(Exception):
    """Raised when data integrity checks fail."""
    pass

class ERR_CPU_LOAD_FAIL(Exception):
    """Raised when CPU model loading fails due to OOM or other issues."""
    pass

class STALENESS_OVERFLOW(Exception):
    """Raised when staleness exceeds the buffer capacity."""
    pass

class ERR_SEED_UNSTABLE(Exception):
    """Raised when no stable seed can be found after maximum attempts."""
    pass
