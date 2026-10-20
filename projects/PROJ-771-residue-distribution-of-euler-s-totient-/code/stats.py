"""
Statistics module for the Euler Totient residue‑distribution pipeline.

This module implements the public API required by the test‑suite:
- calculate_chi_squared_statistic
- check_bin_counts_and_fallback
- run_chi_squared_test
- run_chi_squared_goodness_of_fit (legacy wrapper)
- block_bootstrap_residues
- calculate_deviation_D
- run_block_bootstrap_deviation_test
- StatisticalResult (dataclass with JSON serialisation)
- run_full_statistical_analysis
- save_statistical_result / load_statistical_result
"""

import json
import logging
import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.stats import chi2, multinomial_test

from exceptions import ResearchIncompleteError, MemoryLimitExceeded

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _pin_random_seed(seed: int) -> None:
    """Pin both the Python ``random`` and NumPy RNGs."""
    random.seed(seed)
    np.random.seed(seed)

# ----------------------------------------------------------------------
# Core statistical calculations
# ----------------------------------------------------------------------
def calculate_chi_squared_statistic(
    residue_counts: Dict[int, int], prime: int, N: int
) -> Tuple[float, float]:
    """
    Compute the chi‑squared statistic and its asymptotic p‑value.

    Parameters
    ----------
    residue_counts : dict[int, int]
        Observed frequencies for each residue class.
    prime : int
        Modulus (must be one of the supported small primes).
    N : int
        Total number of observations (sum of all counts).

    Returns
    -------
    tuple[float, float]
        (chi_sq, p_value) where ``p_value`` is based on the chi‑squared
        distribution with ``prime‑1`` degrees of freedom.
    """
    expected = N / prime
    chi_sq = sum(
        ((residue_counts.get(r, 0) - expected) ** 2) / expected
        for r in range(prime)
    )
    p_val = 1.0 - chi2.cdf(chi_sq, df=prime - 1)
    return chi_sq, p_val

def check_bin_counts_and_fallback(
    residue_counts: Dict[int, int], prime: int, N: int
) -> Tuple[bool, str]:
    """
    Determine whether the chi‑squared approximation is unreliable.

    Returns
    -------
    tuple[bool, str]
        ``(needs_fallback, method)`` where ``needs_fallback`` is ``True`` if
        any expected bin count is < 5.  ``method`` is the string the test
        driver should report: ``"monte_carlo"`` for a fallback, ``"exact"``
        otherwise.
    """
    expected = N / prime
    if expected < 5:
        return True, "monte_carlo"
    else:
        return False, "exact"

def exact_multinomial_test(residue_counts: Dict[int, int], prime: int) -> float:
    """
    Perform an exact multinomial goodness‑of‑fit test using SciPy.

    Returns
    -------
    float
        Exact two‑sided p‑value.
    """
    counts = [residue_counts.get(r, 0) for r in range(prime)]
    prob = [1 / prime] * prime
    return float(multinomial_test(counts, p=prob))

def run_chi_squared_test(
    observed_counts: Dict[int, int],
    prime: int,
    M: int = 1000,
    seed: Optional[int] = None,
) -> Tuple[float, str]:
    """
    Perform a chi‑squared goodness‑of‑fit test.

    Parameters
    ----------
    observed_counts : dict[int, int]
        Observed residue frequencies.
    prime : int
        Modulus.
    M : int, optional
        Number of Monte‑Carlo simulations (default 1000).  Ignored when the
        exact test is used.
    seed : int, optional
        Random seed for reproducibility.

    Returns
    -------
    tuple[float, str]
        ``(p_value, method)`` where ``method`` is one of
        ``"chi_squared_monte_carlo"``, ``"chi_squared_exact"``, or
        ``"chi_squared_asymptotic"``.
    """
    if seed is not None:
        _pin_random_seed(seed)

    N = sum(observed_counts.values())
    chi_sq, asymp_p = calculate_chi_squared_statistic(observed_counts, prime, N)

    fallback, _ = check_bin_counts_and_fallback(observed_counts, prime, N)

    if fallback:
        # Use exact multinomial test
        p_val = exact_multinomial_test(observed_counts, prime)
        method = "chi_squared_exact"
    else:
        # Monte‑Carlo refinement
        sims = np.random.multinomial(N, [1 / prime] * prime, size=M)
        sim_chi = np.sum(((sims - (N / prime)) ** 2) / (N / prime), axis=1)
        mc_p = (np.sum(sim_chi >= chi_sq) + 1) / (M + 1)
        p_val = mc_p
        method = "chi_squared_monte_carlo"

    return p_val, method

def run_chi_squared_goodness_of_fit(
    observed_counts: Dict[int, int],
    prime: int,
    M: int = 1000,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Legacy wrapper retained for backward compatibility.
    Returns a dictionary with the same keys as the historic implementation.
    """
    p_val, method = run_chi_squared_test(observed_counts, prime, M=M, seed=seed)
    chi_sq, _ = calculate_chi_squared_statistic(observed_counts, prime, sum(observed_counts.values()))
    return {
        "chi_squared_statistic": chi_sq,
        "p_value": p_val,
        "method": method,
        "degrees_of_freedom": prime - 1,
    }

# ----------------------------------------------------------------------
# Block‑bootstrap utilities
# ----------------------------------------------------------------------
def block_bootstrap_residues(
    residue_sequence: List[int],
    block_size: int,
    num_samples: int,
) -> List[List[int]]:
    """
    Perform a contiguous‑block bootstrap on ``residue_sequence``.
    """
    N = len(residue_sequence)
    if block_size <= 0:
        raise ValueError("block_size must be a positive integer")
    num_blocks = int(np.ceil(N / block_size))
    # Pad the sequence so that it can be divided evenly into blocks
    padded = residue_sequence + [residue_sequence[-1]] * (num_blocks * block_size - N)
    blocks = [
        padded[i * block_size : (i + 1) * block_size] for i in range(num_blocks)
    ]

    bootstrap_samples: List[List[int]] = []
    for _ in range(num_samples):
        sampled_indices = np.random.randint(0, num_blocks, size=num_blocks)
        sample: List[int] = []
        for idx in sampled_indices:
            sample.extend(blocks[idx])
        bootstrap_samples.append(sample[:N])
    return bootstrap_samples

def calculate_deviation_D(
    observed_counts: Dict[int, int], prime: int, N: int
) -> float:
    """Maximum absolute deviation between observed counts and the uniform expectation."""
    expected = N / prime
    return max(abs(observed_counts.get(r, 0) - expected) for r in range(prime))

def run_block_bootstrap_deviation_test(
    observed_counts: Dict[int, int],
    residue_sequence: List[int],
    prime: int,
    N: int,
    block_size: Optional[int] = None,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: Optional[int] = None,
) -> Tuple[float, bool]:
    """
    Compute deviation magnitude ``D`` and its bootstrap p‑value.

    Returns
    -------
    tuple[float, bool]
        ``(p_value, pass_flag)`` where ``pass_flag`` is ``True`` if
        ``p_value >= alpha``.
    """
    if seed is not None:
        _pin_random_seed(seed)

    if N < 100:
        D_obs = calculate_deviation_D(observed_counts, prime, N)
        return D_obs, D_obs >= alpha

    if block_size is None:
        block_size = max(1, int(np.sqrt(N)))

    D_obs = calculate_deviation_D(observed_counts, prime, N)
    boot_sequences = block_bootstrap_residues(residue_sequence, block_size, num_samples)

    boot_D = []
    for seq in boot_sequences:
        boot_counts = {r: 0 for r in range(prime)}
        for r in seq:
            boot_counts[r] = boot_counts.get(r, 0) + 1
        boot_D.append(calculate_deviation_D(boot_counts, prime, N))

    p_val = (np.sum(np.array(boot_D) >= D_obs) + 1) / (num_samples + 1)
    return p_val, p_val >= alpha

# ----------------------------------------------------------------------
# Data class for statistical results
# ----------------------------------------------------------------------
@dataclass
class StatisticalResult:
    """
    Container for the result of a statistical analysis for a single prime.

    The fields are deliberately aligned with the expectations of the
    unit‑ and integration‑tests.
    """
    prime: int
    N: int
    chi_squared_statistic: float
    chi_squared_p_value: float
    exact_test_p_value: Optional[float]
    block_bootstrap_p_value: Optional[float]
    error_term_residual: float
    primary_pass_fail: bool
    bonferroni_pass_fail: bool
    degrees_of_freedom: int
    observed_counts: Dict[int, int]
    expected_counts: Dict[int, float]
    method: str

    def to_json(self) -> str:
        """Serialise the result to a JSON string."""
        return json.dumps(asdict(self), indent=2)

# ----------------------------------------------------------------------
# High‑level analysis driver used by the orchestrator
# ----------------------------------------------------------------------
def run_full_statistical_analysis(
    observed_counts: Dict[int, int],
    prime: int,
    N: int,
    config: Optional[Dict[str, Any]] = None,
) -> StatisticalResult:
    """
    Execute the full statistical pipeline for a single residue dataset.

    Parameters
    ----------
    observed_counts : dict[int, int]
        Frequency map of residues.
    prime : int
        Modulus.
    N : int
        Total number of observations.
    config : dict, optional
        May contain ``seed``, ``chi2_mc_samples`` and ``bootstrap_samples``.
        Missing keys fall back to sensible defaults.

    Returns
    -------
    StatisticalResult
        Dataclass instance populated with all computed metrics.
    """
    if config is None:
        config = {}

    seed = config.get("seed")
    if seed is not None:
        _pin_random_seed(seed)

    # ------------------------------------------------------------------
    # Deviation test (block bootstrap)
    # ------------------------------------------------------------------
    # Build a deterministic residue sequence from the multiset of residues
    residue_sequence = sum(
        ([r] * observed_counts.get(r, 0) for r in range(prime)), []
    )
    bootstrap_samples = config.get("bootstrap_samples", 1000)
    p_bootstrap, _ = run_block_bootstrap_deviation_test(
        observed_counts,
        residue_sequence,
        prime,
        N,
        block_size=None,
        num_samples=bootstrap_samples,
        alpha=0.05,
        seed=seed,
    )

    # ------------------------------------------------------------------
    # Chi‑squared test
    # ------------------------------------------------------------------
    chi2_mc_samples = config.get("chi2_mc_samples", 1000)
    chi_p, chi_method = run_chi_squared_test(
        observed_counts, prime, M=chi2_mc_samples, seed=seed
    )
    chi_sq, _ = calculate_chi_squared_statistic(observed_counts, prime, N)

    # ------------------------------------------------------------------
    # Assemble result
    # ------------------------------------------------------------------
    expected_counts = {r: N / prime for r in range(prime)}
    error_term_residual = (
        float("inf")
        if N == 0
        else abs(calculate_deviation_D(observed_counts, prime, N))
        / (np.sqrt(N) if N > 0 else 1)
    )
    primary_pass = p_bootstrap >= 0.05
    bonferroni_pass = p_bootstrap >= (0.05 / 4)

    result = StatisticalResult(
        prime=prime,
        N=N,
        chi_squared_statistic=chi_sq,
        chi_squared_p_value=chi_p,
        exact_test_p_value=None if chi_method != "chi_squared_exact" else chi_p,
        block_bootstrap_p_value=p_bootstrap,
        error_term_residual=error_term_residual,
        primary_pass_fail=primary_pass,
        bonferroni_pass_fail=bonferroni_pass,
        degrees_of_freedom=prime - 1,
        observed_counts=observed_counts,
        expected_counts=expected_counts,
        method=chi_method,
    )
    return result

# ----------------------------------------------------------------------
# Persistence helpers
# ----------------------------------------------------------------------
def save_statistical_result(result: StatisticalResult, path: str) -> None:
    """Write a ``StatisticalResult`` to ``path`` as JSON."""
    with open(path, "w") as f:
        json.dump(asdict(result), f, indent=2)

def load_statistical_result(path: str) -> StatisticalResult:
    """Read a ``StatisticalResult`` from ``path``."""
    with open(path, "r") as f:
        data = json.load(f)
    return StatisticalResult(**data)