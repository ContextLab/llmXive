"""
Custom exception hierarchy for the Euler Totient residue distribution project.
"""

class TotientError(Exception):
    """Base class for errors raised during totient computation."""
    def __init__(self, message: str = "An error occurred in totient computation"):
        super().__init__(message)

class MemoryLimitExceeded(TotientError):
    """Raised when the MemoryGuard detects usage beyond the allowed limit."""
    def __init__(self, limit_mb: float, usage_mb: float):
        message = (
            f"Memory limit exceeded: allowed {limit_mb:.2f} MB, "
            f"current usage {usage_mb:.2f} MB"
        )
        super().__init__(message)
        self.limit_mb = limit_mb
        self.usage_mb = usage_mb

class InvalidPrimeError(TotientError):
    """Raised when a non‑supported prime modulus is supplied."""
    def __init__(self, prime: int):
        message = f"Invalid prime modulus {prime}. Supported: 3, 5, 7, 11."
        super().__init__(message)
        self.prime = prime

# Additional exception used by benchmark validation tests
class BenchmarkFailure(Exception):
    """
    Raised when a benchmark exceeds the allowed wall‑clock time.
    
    Attributes
    ----------
    elapsed_time : float
        The measured elapsed time in seconds.
    limit : float
        The maximum allowed time in seconds.
    """
    def __init__(self, elapsed_time: float, limit: float = 3600.0):
        self.elapsed_time = elapsed_time
        self.limit = limit
        super().__init__(f"Benchmark failed: {elapsed_time:.2f}s exceeds limit {limit:.2f}s")
