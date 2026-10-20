"""
Synthetic validation utilities for the Euler Totient residue‑distribution pipeline.

This module provides helper functions to generate synthetic uniform and biased
residue count dictionaries, run the full statistical analysis on them, and
produce the pass/fail flag JSON using the existing ``flags`` module.

The functions are deliberately lightweight and rely only on the public API
of ``stats`` and ``flags`` that are already part of the project.
"""

from __future__ import annotations

import os
from typing import Dict

from .stats import (
    run_full_statistical_analysis,
    save_statistical_result,
)
from .flags import generate_flag_from_result

__all__ = [
    "generate_uniform_counts",
    "generate_biased_counts",
    "run_stats_and_flag",
]


def generate_uniform_counts(N: int, prime: int) -> Dict[int, int]:
    """
    Generate a synthetic *uniform* residue frequency map.

    Parameters
    ----------
    N : int
        Total number of observations (must be > 0).
    prime : int
        Modulus (must be one of the supported small primes).

    Returns
    -------
    Dict[int, int]
        Mapping ``residue → count`` where the counts differ by at most one
        (the usual way to distribute ``N`` items uniformly over ``prime``
        classes).

    Notes
    -----
    The function distributes the remainder ``N % prime`` by adding one
    to the first ``remainder`` residues (0, 1, …).  This mirrors how a
    perfectly uniform dataset would appear when ``N`` is not a multiple
    of ``prime``.
    """
    if N <= 0:
        raise ValueError("N must be a positive integer")
    if prime <= 0:
        raise ValueError("prime must be a positive integer")

    base = N // prime
    remainder = N % prime
    counts: Dict[int, int] = {r: base for r in range(prime)}
    for r in range(remainder):
        counts[r] += 1
    return counts


def generate_biased_counts(
    N: int,
    prime: int,
    bias_residue: int = 0,
    bias_factor: float = 1.5,
) -> Dict[int, int]:
    """
    Generate a synthetic *biased* residue frequency map.

    The ``bias_residue`` class receives a larger share of the total
    observations (``bias_factor`` times the uniform expectation).  The
    remaining residues are reduced proportionally so that the total count
    stays exactly ``N``.

    Parameters
    ----------
    N : int
        Total number of observations.
    prime : int
        Modulus (must be one of the supported small primes).
    bias_residue : int, optional
        The residue class to be inflated.  Defaults to ``0``.
    bias_factor : float, optional
        Multiplicative factor by which the biased class is enlarged.
        Must be greater than ``1.0``.  The default ``1.5`` yields a
        50 % increase over the uniform expectation.

    Returns
    -------
    Dict[int, int]
        Frequency map with the specified bias applied.
    """
    if N <= 0:
        raise ValueError("N must be a positive integer")
    if prime <= 0:
        raise ValueError("prime must be a positive integer")
    if not (0 <= bias_residue < prime):
        raise ValueError("bias_residue must be a valid residue class")
    if bias_factor <= 1.0:
        raise ValueError("bias_factor must be greater than 1.0")

    # Start from a uniform baseline
    base = N // prime
    counts: Dict[int, int] = {r: base for r in range(prime)}

    # Compute the extra amount to add to the biased class
    extra = int(base * (bias_factor - 1.0))
    counts[bias_residue] = base + extra

    # Adjust the other classes to keep the total at N
    total = sum(counts.values())
    excess = total - N  # may be positive (need to remove) or zero

    if excess > 0:
        # Reduce the non‑biased residues as evenly as possible
        residues = [r for r in range(prime) if r != bias_residue]
        idx = 0
        while excess > 0 and residues:
            r = residues[idx % len(residues)]
            if counts[r] > 0:
                reduction = min(counts[r], excess)
                counts[r] -= reduction
                excess -= reduction
            idx += 1

    return counts


def run_stats_and_flag(
    observed_counts: Dict[int, int],
    prime: int,
    N: int,
    output_dir: str,
) -> Dict[str, bool]:
    """
    Run the full statistical analysis on a synthetic dataset and generate
    the corresponding ``alpha_pass``/``bonferroni_pass`` flag JSON.

    The function writes two artefacts to ``output_dir``:

    1. ``stats_{prime}_{N}.json`` – the serialized :class:`StatisticalResult`.
    2. ``flag_{prime}_{N}.json`` – the flag file produced by
       :func:`flags.generate_flag_from_result`.

    Parameters
    ----------
    observed_counts : Dict[int, int]
        Synthetic frequency map (output of :func:`generate_uniform_counts`
        or :func:`generate_biased_counts`).
    prime : int
        Modulus used for the analysis.
    N : int
        Total number of observations (should equal ``sum(observed_counts.values())``).
    output_dir : str
        Directory in which to write the temporary JSON artefacts.  The
        directory is created automatically if it does not exist.

    Returns
    -------
    Dict[str, bool]
        The flag dictionary returned by ``generate_flag_from_result``.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Run the statistical pipeline
    result = run_full_statistical_analysis(observed_counts, prime, N)

    # Write the StatisticalResult JSON
    json_path = os.path.join(output_dir, f"stats_{prime}_{N}.json")
    save_statistical_result(result, json_path)

    # Generate and return the flag dict (this also writes the flag file)
    flags = generate_flag_from_result(json_path)
    return flags