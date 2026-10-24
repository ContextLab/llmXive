"""
Sieve module for computing Euler's totient function values and aggregating residues.

Public API
----------
- MemoryGuard: re-exported from ``code.memory_guard`` for backward compatibility.
- ResidueDataset: dataclass representing the JSON schema for residue counts.
- pin_random_seed: pins the global ``random`` seed (legacy helper).
- log_error: logs an error message, optionally annotating the iteration ``n``.
- compute_phi_linear_sieve: linear sieve implementation returning a list ``phi`` where
  ``phi[i] == φ(i)`` for ``0 ≤ i ≤ N``.
- compute_residues: aggregates residues of ``phi_vals`` modulo ``prime``.
- save_residue_dataset / load_residue_dataset: JSON persistence utilities.
- run_sieve_analysis: orchestrates the sieve for a list of primes.

The module is importable both as a top-level module (``import sieve``,
with ``code/`` on ``sys.path``) and as a package member (``code.sieve``).
A small bootstrap at import time ensures sibling modules (``memory_guard``,
``exceptions``) resolve regardless of how the module is loaded.
"""

import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# ----------------------------------------------------------------------
# Import bootstrap – make sibling modules importable no matter how this
# module is loaded (as ``sieve`` or as ``code.sieve``).
# ----------------------------------------------------------------------
_CODE_DIR = str(Path(__file__).resolve().parent)
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

# ----------------------------------------------------------------------
# Compatibility shim – re-export MemoryGuard from the dedicated module
# ----------------------------------------------------------------------
from memory_guard import MemoryGuard  # noqa: F401

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------
from exceptions import InvalidPrimeError, MemoryLimitExceeded

# Ensure imported public classes have docstrings for the docstring‑coverage test.
if not getattr(MemoryGuard, "__doc__", None):
    MemoryGuard.__doc__ = (
        "MemoryGuard monitors the process memory usage and raises "
        "MemoryLimitExceeded when a configured threshold is exceeded."
    )
if not getattr(InvalidPrimeError, "__doc__", None):
    InvalidPrimeError.__doc__ = (
        "InvalidPrimeError is raised when a supplied prime is not among the "
        "supported set {3, 5, 7, 11}."
    )
if not getattr(MemoryLimitExceeded, "__doc__", None):
    MemoryLimitExceeded.__doc__ = (
        "MemoryLimitExceeded signals that the process has exceeded the allowed "
        "memory limit."
    )

# ----------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------
@dataclass
class ResidueDataset:
    """
    Container for residue count data produced by the sieve.

    Attributes
    ----------
    prime_modulus : int
        The prime modulus ``p`` (e.g., 3, 5, 7, 11).
    total_count : int
        Total number of integers processed (the ``N`` bound).
    frequency_map : Dict[int, int]
        Mapping from each residue ``0 … p-1`` to its observed count.
    computation_seed : int
        The random seed used for any stochastic steps (currently a placeholder;
        the real seed is stored elsewhere in the pipeline).
    """
    prime_modulus: int
    total_count: int
    frequency_map: Dict[int, int]
    computation_seed: int

# ----------------------------------------------------------------------
# Legacy seed helper (kept for backward compatibility with older scripts)
# ----------------------------------------------------------------------
def pin_random_seed(seed: int) -> None:
    """Pin the global ``random`` seed (legacy helper)."""
    import random

    random.seed(seed)

# ----------------------------------------------------------------------
# Logging helper
# ----------------------------------------------------------------------
def log_error(message: str, n: Optional[int] = None) -> None:
    """
    Log an error message. If ``n`` is supplied, include it in the log.

    Parameters
    ----------
    message : str
        Human‑readable description of the error.
    n : int, optional
        Iteration index or identifier where the error occurred.
    """
    if n is not None:
        logging.error("n=%s – %s", n, message)
    else:
        logging.error("%s", message)

# ----------------------------------------------------------------------
# Linear sieve for Euler's totient function
# ----------------------------------------------------------------------
def compute_phi_linear_sieve(
    N: int,
    memory_guard: Optional[MemoryGuard] = None
) -> List[int]:
    """
    Compute Euler's totient function φ(n) for all ``1 ≤ n ≤ N`` using the
    linear sieve algorithm.

    The implementation follows the classic O(N) approach:
    - ``phi[1] = 1``.
    - Maintain a list of primes discovered so far.
    - For each integer i, propagate φ values to multiples of i.

    All arithmetic uses Python's arbitrary‑precision ``int`` so no
    overflow can occur for any ``N``.

    Parameters
    ----------
    N : int
        Upper bound of the range (inclusive).
    memory_guard : MemoryGuard, optional
        Guard that is polled every 10 000 iterations.  If the guard
        reports that memory usage exceeds the configured limit,
        a :class:`MemoryLimitExceeded` exception is raised.

    Returns
    -------
    List[int]
        List ``phi`` where ``phi[i]`` equals ``φ(i)`` for ``0 ≤ i ≤ N``.
        ``phi[0]`` is set to ``0`` for convenience.

    Raises
    ------
    MemoryLimitExceeded
        If the memory guard signals that the limit has been crossed
        (either by returning a falsy result from ``check`` or by
        raising ``MemoryLimitExceeded`` itself).
    ValueError
        If ``N`` is less than 1.
    """
    if N < 1:
        raise ValueError("N must be a positive integer")

    # Initialise phi array
    phi: List[int] = [0] * (N + 1)
    phi[0] = 0
    phi[1] = 1
    primes: List[int] = []

    # Helper to poll the memory guard safely.  The guard may raise
    # ``MemoryLimitExceeded`` itself (which propagates unchanged) or
    # return a boolean status.
    def _poll_guard(iteration: int) -> None:
        if memory_guard is None:
            return
        try:
            result = memory_guard.check(iteration)  # type: ignore[arg-type]
        except TypeError:
            result = memory_guard.check()  # type: ignore[call-arg]
        if not result:
            raise MemoryLimitExceeded(
                f"Memory usage exceeded the configured limit at i={iteration}"
            )

    # Linear sieve loop
    for i in range(2, N + 1):
        # Poll memory usage every 10 000 iterations as required.
        if i % 10_000 == 0:
            _poll_guard(i)
        if phi[i] == 0:  # i is prime
            phi[i] = i - 1
            primes.append(i)
        for p in primes:
            if i * p > N:
                break
            if i % p == 0:
                phi[i * p] = phi[i] * p
                break
            else:
                phi[i * p] = phi[i] * (p - 1)
    return phi

# ----------------------------------------------------------------------
# Residue aggregation
# ----------------------------------------------------------------------
def compute_residues(phi_vals: List[int], prime: int) -> Dict[int, int]:
    """
    Aggregate residues of ``phi_vals`` modulo ``prime``.

    Parameters
    ----------
    phi_vals : List[int]
        List of totient values as returned by ``compute_phi_linear_sieve``.
    prime : int
        Modulus (must be one of the supported small primes 3, 5, 7, 11).

    Returns
    -------
    Dict[int, int]
        Mapping ``residue → count`` for all residues in ``0 … prime-1``.
        The sum of all counts equals ``len(phi_vals) - 1`` (entry 0 is
        the unused placeholder for n=0).

    Raises
    ------
    InvalidPrimeError
        If ``prime`` is not one of the supported primes {3, 5, 7, 11}.
    """
    if prime not in (3, 5, 7, 11):
        raise InvalidPrimeError(prime)

    freq: Dict[int, int] = {r: 0 for r in range(prime)}
    # phi_vals[0] corresponds to n=0 (unused); start from 1
    for n in range(1, len(phi_vals)):
        residue = phi_vals[n] % prime
        freq[residue] += 1
    return freq

# ----------------------------------------------------------------------
# Persistence helpers
# ----------------------------------------------------------------------
def save_residue_dataset(
    residue_counts: Dict[int, int],
    prime: int,
    N: int,
    filepath: str,
) -> None:
    """
    Persist a ``ResidueDataset`` as JSON.

    Parameters
    ----------
    residue_counts : Dict[int, int]
        Frequency map produced by ``compute_residues``.
    prime : int
        Modulus used for the computation.
    N : int
        Number of integers processed.
    filepath : str
        Destination file path (parent directories are created if needed).
    """
    dataset = ResidueDataset(
        prime_modulus=prime,
        total_count=N,
        frequency_map=residue_counts,
        computation_seed=0,  # placeholder – real seed is pinned elsewhere
    )
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(dataset), f, indent=2)

def load_residue_dataset(filepath: str) -> ResidueDataset:
    """
    Load a ``ResidueDataset`` from a JSON file.

    Parameters
    ----------
    filepath : str
        Path to the JSON file.

    Returns
    -------
    ResidueDataset
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    # JSON keys are strings; convert back to int for the frequency map.
    if "frequency_map" in data and isinstance(data["frequency_map"], dict):
        data["frequency_map"] = {
            int(k): int(v) for k, v in data["frequency_map"].items()
        }
    return ResidueDataset(**data)

# ----------------------------------------------------------------------
# High-level orchestration helper
# ----------------------------------------------------------------------
def run_sieve_analysis(
    N: int,
    primes: List[int],
    output_dir: str,
    memory_guard: Optional[MemoryGuard] = None,
) -> Dict[int, Dict[str, Any]]:
    """
    Run the sieve for a list of primes, saving each result.

    Parameters
    ----------
    N : int
        Upper bound of the range (inclusive).
    primes : List[int]
        List of prime moduli to process.
    output_dir : str
        Directory in which to write the JSON residue files.
    memory_guard : MemoryGuard, optional
        Guard used during the totient computation.

    Returns
    -------
    Dict[int, Dict[str, Any]]
        Mapping ``prime → {status: 'success'|'failed'}``.  If the
        underlying computation raises, the function records a failure
        and does not write any file.
    """
    results: Dict[int, Dict[str, Any]] = {}
    phi_vals: Optional[List[int]] = None
    for prime in primes:
        try:
            if phi_vals is None:
                phi_vals = compute_phi_linear_sieve(N, memory_guard=memory_guard)
            residue_counts = compute_residues(phi_vals, prime)
            outfile = Path(output_dir) / f"residues_{prime}_{N}.json"
            save_residue_dataset(residue_counts, prime, N, str(outfile))
            results[prime] = {"status": "success"}
        except Exception as exc:
            results[prime] = {"status": "failed", "error": str(exc)}
    return results
