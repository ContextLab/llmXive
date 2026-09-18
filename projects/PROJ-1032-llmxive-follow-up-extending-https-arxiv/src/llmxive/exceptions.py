"""Custom exceptions for llmXive project."""

class DATA_INTEGRITY_ERROR(Exception):
    """Raised when data integrity checks fail."""
    pass

class ERR_CPU_LOAD_FAIL(Exception):
    """Raised when CPU model loading fails (OOM)."""
    pass

class STALENESS_OVERFLOW(Exception):
    """Raised when staleness exceeds buffer limits."""
    pass

class ERR_SEED_UNSTABLE(Exception):
    """Raised when a seed fails stability verification."""
    pass
