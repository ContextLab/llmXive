"""Custom exceptions for llmXive."""

class DATA_INTEGRITY_ERROR(Exception):
    """Raised when data integrity checks fail (e.g., overlap, checksum mismatch)."""
    pass

class ERR_CPU_LOAD_FAIL(Exception):
    """Raised when CPU model loading fails due to OOM or other resource constraints."""
    pass

class STALENESS_OVERFLOW(Exception):
    """Raised when staleness exceeds the configured buffer limits."""
    pass

class ERR_SEED_UNSTABLE(Exception):
    """Raised when a seed fails stability verification after max retries."""
    pass
