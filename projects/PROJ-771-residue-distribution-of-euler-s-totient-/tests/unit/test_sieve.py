"""
Unit tests for the sieve module (task T006).

Covers:
(a) exact φ values for n = 1 … 10,
(b) correct residue counts for primes 3, 5, 7, 11 (checked against an
    independent brute-force gcd-based reference implementation),
(c) proper MemoryLimitExceeded raising when a forced low memory limit
    is supplied.
"""
import sys
from math import gcd
from pathlib import Path

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from sieve import compute_phi_linear_sieve, compute_residues, MemoryGuard
from exceptions import MemoryLimitExceeded


def reference_phi(n: int) -> int:
    """Independent brute-force reference: φ(n) = #{k ≤ n : gcd(k, n) = 1}."""
    return sum(1 for k in range(1, n + 1) if gcd(k, n) == 1)


def test_phi_values_1_to_10():
    """(a) Exact φ values for n = 1 … 10."""
    phi = compute_phi_linear_sieve(10)
    expected = [1, 1, 2, 2, 4, 2, 6, 4, 6, 4]
    assert [phi[n] for n in range(1, 11)] == expected


def test_phi_against_gcd_reference():
    """Cross-check the linear sieve against the brute-force definition."""
    N = 200
    phi = compute_phi_linear_sieve(N)
    for n in range(1, N + 1):
        assert phi[n] == reference_phi(n), f"phi({n}) mismatch"


def test_phi_invalid_N():
    """N < 1 must raise ValueError."""
    with pytest.raises(ValueError):
        compute_phi_linear_sieve(0)


@pytest.mark.parametrize("prime", [3, 5, 7, 11])
def test_residue_counts(prime):
    """(b) Correct residue counts for primes 3, 5, 7, 11."""
    N = 100
    phi = compute_phi_linear_sieve(N)
    counts = compute_residues(phi, prime)

    # Independent reference computed via gcd-based φ.
    ref = {r: 0 for r in range(prime)}
    for n in range(1, N + 1):
        ref[reference_phi(n) % prime] += 1

    assert counts == ref
    assert sum(counts.values()) == N
    assert set(counts.keys()) == set(range(prime))


def test_compute_residues_rejects_unsupported_prime():
    """Only primes 3, 5, 7, 11 are supported."""
    phi = compute_phi_linear_sieve(10)
    with pytest.raises(Exception):
        compute_residues(phi, 13)


def test_memory_guard_trigger_low_limit():
    """(c) A forced low memory limit must raise MemoryLimitExceeded."""
    # A 1 MB limit is far below the process's actual RSS, so the guard
    # must trigger when polled (every 10 000 iterations).
    guard = MemoryGuard(limit_mb=1, check_interval=1)
    with pytest.raises(MemoryLimitExceeded):
        compute_phi_linear_sieve(20_000, memory_guard=guard)


def test_memory_guard_no_trigger_generous_limit():
    """A generous limit must let the sieve complete normally."""
    guard = MemoryGuard(limit_mb=100_000, check_interval=1)
    phi = compute_phi_linear_sieve(20_000, memory_guard=guard)
    assert phi[20_000] == reference_phi(20_000)