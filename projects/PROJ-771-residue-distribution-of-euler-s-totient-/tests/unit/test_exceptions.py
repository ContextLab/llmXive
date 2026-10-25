"""
Unit tests for the custom exception hierarchy.
"""

import pytest
from code.exceptions import TotientError, MemoryLimitExceeded, InvalidPrimeError, BenchmarkFailure

def test_totient_error_message():
    exc = TotientError("custom message")
    assert str(exc) == "custom message"

def test_memory_limit_exceeded_message():
    exc = MemoryLimitExceeded(limit_mb=100.0, usage_mb=120.5)
    assert "Memory limit exceeded" in str(exc)
    assert "100.00 MiB" in str(exc)
    assert "120.50 MiB" in str(exc)

def test_invalid_prime_error_message():
    exc = InvalidPrimeError(13)
    assert "Invalid prime modulus 13" in str(exc)

def test_benchmark_failure_message():
    exc = BenchmarkFailure(elapsed_time=7200.0, limit=3600.0)
    assert "Benchmark failed" in str(exc)
    assert "7200.00s" in str(exc)