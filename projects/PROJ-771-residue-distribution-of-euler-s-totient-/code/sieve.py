"""
Sieve module for Euler's totient function and residue aggregation.

Provides the core linear sieve implementation, residue counting, and
deterministic JSON persistence required by the pipeline.  The module
uses :class:`memory_guard.MemoryGuard` to enforce the memory limit
during the sieve and raises :class:`exceptions.MemoryLimitExceeded`
when the limit is breached.  It also detects logical inconsistencies
in the totient computation and halts execution, logging the offending
index ``n`` before raising :class:`exceptions.TotientError`.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from memory_guard import MemoryGuard
from exceptions import InvalidPrimeError, MemoryLimitExceeded, TotientError

# ----------------------------------------------------------------------
# Legacy helper – retained for compatibility with older code paths.
# ----------------------------------------------------------------------
def pin_random_seed(seed: int) -> None:
    """
    Pin the global ``random`` seed (legacy helper).

    Parameters
    ----------
    seed : int
        Seed value for the standard library ``random`` module.
    """
    random.seed(seed)

# ----------------------------------------------------------------------
# Simple error logger used throughout the module.
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
    logger = logging.getLogger(__name__)
    if n is not None:
        logger.error("%s (at n=%s)", message, n)
    else:
        logger.error(message)

# ----------------------------------------------------------------------
# Data model for a residue dataset.
# ----------------------------------------------------------------------
@dataclass
class ResidueDataset:
    """
    Simple container for the residues of φ(n) modulo a prime.

    Attributes
    ----------
    prime : int
        The modulus used.
    N : int
        Number of integers processed (range 1…N).
    frequency_map : Dict[int, int]
        Mapping ``residue → count``.
    """
    prime: int
    N: int
    frequency_map: Dict[int, int]

    def to_json(self) -> str:
        """Serialise the dataset to a JSON string with deterministic ordering."""
        data = {
            "prime": self.prime,
            "N": self.N,
            "frequency_map": {str(k): v for k, v in sorted(self.frequency_map.items())},
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

# ----------------------------------------------------------------------
# Linear sieve for Euler's totient function.
# ----------------------------------------------------------------------
def compute_phi_linear_sieve(
    N: int, memory_guard: Optional[MemoryGuard] = None
) -> List[int]:
    """
    Compute φ values for all ``1 ≤ n ≤ N`` using the classic O(N) linear sieve.

    The implementation detects logical errors (e.g. a totient value of
    zero for ``n > 1``) and halts execution, logging the offending ``n``
    before raising :class:`exceptions.TotientError`.

    Parameters
    ----------
    N : int
        Upper bound of the range (inclusive). Must be ≥ 1.
    memory_guard : MemoryGuard, optional
        Guard that is polled every 10 000 iterations.  If the guard
        signals that memory usage exceeds the configured limit, a
        :class:`MemoryLimitExceeded` exception is raised.

    Returns
    -------
    List[int]
        List ``phi`` where ``phi[i]`` equals ``φ(i)`` for ``0 ≤ i ≤ N``.
        ``phi[0]`` is set to ``0`` for convenience.

    Raises
    ------
    ValueError
        If ``N`` is less than 1.
    MemoryLimitExceeded
        Propagated from the ``MemoryGuard`` when the memory threshold is crossed.
    TotientError
        If a logical inconsistency is detected in the totient values.
    """
    if N < 1:
        raise ValueError("N must be a positive integer")

    phi: List[int] = [0] * (N + 1)
    phi[1] = 1
    primes: List[int] = []

    for i in range(2, N + 1):
        if phi[i] == 0:
            # i is prime
            phi[i] = i - 1
            primes.append(i)

            # Sanity check: a prime's totient must be i-1 (>0)
            if phi[i] <= 0:
                log_error("Totient computation error: phi is non‑positive for prime", i)
                raise TotientError(f"Totient error at n={i}")

        for p in primes:
            if i * p > N:
                break
            if i % p == 0:
                phi[i * p] = phi[i] * p
                # Consistency check for the composite case where p divides i
                if phi[i * p] <= 0:
                    log_error("Totient computation error: non‑positive phi for composite", i * p)
                    raise TotientError(f"Totient error at n={i * p}")
                break
            else:
                phi[i * p] = phi[i] * (p - 1)
                if phi[i * p] <= 0:
                    log_error("Totient computation error: non‑positive phi for composite", i * p)
                    raise TotientError(f"Totient error at n={i * p}")

        # Poll the memory guard at the configured interval.
        if memory_guard is not None:
            memory_guard.check(iteration=i)

    # Final sanity check: ensure no phi entry (except phi[0]) is zero.
    for n in range(2, N + 1):
        if phi[n] == 0:
            log_error("Totient computation error: phi remains zero", n)
            raise TotientError(f"Totient error at n={n}")

    return phi

# ----------------------------------------------------------------------
# Residue aggregation.
# ----------------------------------------------------------------------
_SUPPORTED_PRIMES = {3, 5, 7, 11}

def compute_residues(phi_vals: List[int], prime: int) -> Dict[int, int]:
    """
    Aggregate residues of ``phi_vals`` modulo ``prime``.

    Parameters
    ----------
    phi_vals : List[int]
        List of totient values as returned by ``compute_phi_linear_sieve``.
    prime : int
        Modulus (must be one of the supported small primes).

    Returns
    -------
    Dict[int, int]
        Mapping ``residue → count`` for all residues ``0 … prime‑1``.
        The sum of all counts equals ``len(phi_vals) - 1`` (entry 0 is
        the unused placeholder for n=0).

    Raises
    ------
    InvalidPrimeError
        If ``prime`` is not one of the supported primes {3, 5, 7, 11}.
    """
    if prime not in _SUPPORTED_PRIMES:
        raise InvalidPrimeError(
            f"Unsupported prime {prime}. Supported primes are {sorted(_SUPPORTED_PRIMES)}"
        )

    counts: Dict[int, int] = {r: 0 for r in range(prime)}
    # phi_vals[0] is a placeholder; start from index 1.
    for n in range(1, len(phi_vals)):
        residue = phi_vals[n] % prime
        counts[residue] += 1
    return counts

# ----------------------------------------------------------------------
# Deterministic JSON persistence.
# ----------------------------------------------------------------------
def save_residue_dataset(
    residue_counts: Dict[int, int],
    prime: int,
    N: int,
    filepath: str,
) -> None:
    """
    Persist a ``ResidueDataset`` as JSON.

    The output uses ``sort_keys=True`` and writes integer keys as strings
    to guarantee deterministic byte‑wise output across runs.

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
    dataset = ResidueDataset(prime=prime, N=N, frequency_map=residue_counts)
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Use the deterministic ``to_json`` method.
    with path.open("w", encoding="utf-8") as f:
        f.write(dataset.to_json())

# ----------------------------------------------------------------------
# Loading a residue dataset.
# ----------------------------------------------------------------------
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

    # Keys in the JSON are stored as strings; convert back to ints.
    freq_map = {int(k): int(v) for k, v in data["frequency_map"].items()}
    return ResidueDataset(prime=int(data["prime"]), N=int(data["N"]), frequency_map=freq_map)

# ----------------------------------------------------------------------
# End‑to‑end sieve analysis for a collection of primes.
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
        Mapping ``prime → {status: 'success'|'failed', 'path': <filepath>}``.
    """
    results: Dict[int, Dict[str, Any]] = {}
    # Compute φ once – reuse for all primes.
    phi_vals = compute_phi_linear_sieve(N, memory_guard=memory_guard)

    for prime in primes:
        try:
            residues = compute_residues(phi_vals, prime)
            out_path = Path(output_dir) / f"residues_{prime}_{N}.json"
            save_residue_dataset(residues, prime, N, str(out_path))
            results[prime] = {"status": "success", "path": str(out_path)}
        except Exception as exc:
            # Record failure but continue with other primes.
            results[prime] = {"status": "failed", "error": str(exc)}
    return results