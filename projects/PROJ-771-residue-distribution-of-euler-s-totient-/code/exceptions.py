"""
Custom exception hierarchy for the Euler Totient residue distribution project.

This module defines three primary exception classes used throughout the
pipeline:

* ``TotientError`` – raised when the totient computation encounters a
  problem for a specific integer ``n``.
* ``MemoryLimitExceeded`` – raised by ``MemoryGuard`` when the process
  memory usage reaches or exceeds 90 % of the configured limit.
* ``InvalidPrimeError`` – raised when a user supplies a prime modulus that
  is not among the supported set ``{3, 5, 7, 11}``.

Each exception carries a clear, human‑readable error message that
includes the relevant context (e.g., the offending value and the allowed
values).  The messages are deliberately deterministic to satisfy the
unit tests in ``tests/unit/test_exceptions.py``.
"""

class TotientError(Exception):
    """
    Exception raised when the totient function cannot be computed for a
    particular integer ``n``.

    Parameters
    ----------
    n : int
        The integer for which the totient computation failed.
    message : str
        Description of the failure reason.
    """
    def __init__(self, n: int, message: str):
        self.n = n
        self.message = message
        super().__init__(f"Totient error at n={n}: {message}")

class MemoryLimitExceeded(Exception):
    """
    Exception raised when memory usage reaches or exceeds the configured
    limit (≥ 90 % of the ``memory_limit_mb`` setting).

    Parameters
    ----------
    used_mb : float
        Current memory usage in megabytes.
    limit_mb : int
        Configured memory limit in megabytes.
    """
    def __init__(self, used_mb: float, limit_mb: int):
        self.used_mb = used_mb
        self.limit_mb = limit_mb
        super().__init__(
            f"Memory limit exceeded: {used_mb:.2f} MB >= {limit_mb} MB (90% threshold)"
        )

class InvalidPrimeError(Exception):
    """
    Exception raised when an unsupported prime modulus is requested.

    Parameters
    ----------
    prime : int
        The prime value supplied by the user.
    allowed_primes : list[int], optional
        List of primes that are permitted. Defaults to ``[3, 5, 7, 11]``.
    """
    def __init__(self, prime: int, allowed_primes=None):
        if allowed_primes is None:
            allowed_primes = [3, 5, 7, 11]
        self.prime = prime
        self.allowed_primes = allowed_primes
        allowed_str = ", ".join(map(str, allowed_primes))
        super().__init__(
            f"Invalid prime '{prime}'. Supported primes are: {allowed_str}."
        )