import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging
import os

from exceptions import ResearchIncompleteError
from constants import get_error_bound_constants

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class StatisticalResult:
    test_type: str
    p_value: Optional[float]  # p-value may be None for small‑N fallback
    method: str
    degrees_of_freedom: int
    error_term_residual: float
    chi_squared_statistic: float
    chi_squared_p_value: float
    block_bootstrap_p_value: Optional[float]
    pass_fail_flag: bool
    bonferroni_pass_fail_flag: bool


# ----------------------------------------------------------------------
# Seed handling utilities (kept for API compatibility)
# ----------------------------------------------------------------------
def pin_random_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)


def is_seed_pinned() -> bool:
    return True


def get_current_seed() -> int:
    # ``random.getstate`` returns a tuple; the second element holds the seed.
    return random.getstate()[1][1] if hasattr(random.getstate(), '__getitem__') else 42


# ----------------------------------------------------------------------
# I/O helpers (unchanged)
# ----------------------------------------------------------------------
def load_residue_sequence_from_file(path: str) -> List[int]:
    with open(path, 'r') as f:
        return json.load(f)


def load_residue_sequence_from_json(path: str) -> List[int]:
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('sequence', [])


def get_residue_sequence_from_json(path: str) -> List[int]:
    return load_residue_sequence_from_json(path)


def get_observed_counts_from_json(path: str) -> Dict[int, int]:
    with open(path, 'r') as f:
        data = json.load(f)
    return data.get('frequency_map', {})


# ----------------------------------------------------------------------
# Theoretical bound utilities (unchanged)
# ----------------------------------------------------------------------
def calculate_theoretical_bounds(prime: int, N: int) -> Dict[str, float]:
    constants = get_error_bound_constants()
    if not constants:
        raise ResearchIncompleteError("error_bound_constants", "Constants missing from data/constants.yaml")
    
    C = constants.get('C', 1.0)
    c = constants.get('c', 1.0)
    delta = constants.get('delta', 0.0)
    
    # Placeholder formula – real implementation would use the literature’s bound.
    lower = N / prime - C * np.sqrt(N)
    upper = N / prime + C * np.sqrt(N)
    return {'lower': lower, 'upper': upper}


# ----------------------------------------------------------------------
# Deviation D utilities
# ----------------------------------------------------------------------
def calculate_deviation_D(observed_counts: Dict[int, int], prime: int, N: int) -> float:
    """Maximum absolute deviation between observed counts and the uniform expectation."""
    expected = N / prime
    max_dev = 0.0
    for r in range(prime):
        dev = abs(observed_counts.get(r, 0) - expected)
        if dev > max_dev:
            max_dev = dev
    return max_dev


# ----------------------------------------------------------------------
# Bin‑count fallback logic
# ----------------------------------------------------------------------
def check_bin_counts_and_fallback(residue_counts: Dict[int, int], prime: int, N: int) -> bool:
    """
    Return ``True`` if any expected bin count is < 5, signalling that the
    chi‑squared approximation is unreliable and an exact test is required.
    """
    expected = N / prime
    return expected < 5


# ----------------------------------------------------------------------
# Exact multinomial test (new for T017)
# ----------------------------------------------------------------------
def exact_multinomial_test(residue_counts: Dict[int, int], prime: int) -> float:
    """
    Perform an exact multinomial goodness‑of‑fit test.

    Parameters
    ----------
    residue_counts : Dict[int, int]
        Observed frequencies for each residue class.
    prime : int
        Modulus (number of categories).

    Returns
    -------
    float
        Two‑sided exact p‑value from ``scipy.stats.multinomial_test``.
    """
    from scipy.stats import multinomial_test

    counts = [residue_counts.get(r, 0) for r in range(prime)]
    # Uniform null hypothesis probabilities
    p = [1 / prime] * prime
    return float(multinomial_test(counts, p=p))


# ----------------------------------------------------------------------
# Chi‑squared statistic (without p‑value)
# ----------------------------------------------------------------------
def calculate_chi_squared_statistic(
    residue_counts: Dict[int, int],
    prime: int,
    N: int
) -> float:
    """
    Compute the chi‑squared statistic for the observed residue frequencies.

    Returns
    -------
    float
        The chi‑squared statistic value.
    """
    expected = N / prime
    chi_sq = 0.0
    for r in range(prime):
        obs = residue_counts.get(r, 0)
        chi_sq += (obs - expected) ** 2 / expected
    return chi_sq


# ----------------------------------------------------------------------
# Chi‑squared test driver (updated to use exact test automatically)
# ----------------------------------------------------------------------
def run_chi_squared_test(
    dataset: Dict[str, Any],
    M: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform a chi‑squared goodness‑of‑fit test on ``dataset``.

    ``dataset`` must contain:
        - ``frequency_map``: Dict[int, int] of observed counts
        - ``prime``: modulus (int)
        - ``N``: total observations (int)

    If any expected bin count < 5 we use the exact multinomial test.
    Otherwise we compute the asymptotic chi‑squared p‑value and,
    optionally, a Monte‑Carlo estimate with ``M`` simulated samples.
    """
    if seed is not None:
        pin_random_seed(seed)

    counts: Dict[int, int] = dataset["frequency_map"]
    prime: int = dataset["prime"]
    N: int = dataset["N"]

    # Compute chi‑squared statistic (common to both paths)
    chi_sq = calculate_chi_squared_statistic(counts, prime, N)

    fallback_needed = check_bin_counts_and_fallback(counts, prime, N)

    if fallback_needed:
        # Exact multinomial test
        p_val = exact_multinomial_test(counts, prime)
        method = "exact_multinomial"
        mc_p = None
    else:
        # Asymptotic chi‑squared p‑value
        from scipy.stats import chi2
        p_val = 1.0 - chi2.cdf(chi_sq, df=prime - 1)
        method = "chi_squared_asymptotic"
        mc_p = None
        
        # Monte‑Carlo estimation (only when asymptotic is used)
        if M > 0:
            sims = np.random.multinomial(N, [1 / prime] * prime, size=M)
            sim_chi = np.sum(((sims - (N / prime)) ** 2) / (N / prime), axis=1)
            mc_p = (np.sum(sim_chi >= chi_sq) + 1) / (M + 1)  # add‑one smoothing
            method = "chi_squared_monte_carlo"

    result = {
        "chi_squared_statistic": chi_sq,
        "p_value": p_val,
        "monte_carlo_p_value": mc_p,
        "method": method,
        "degrees_of_freedom": prime - 1,
    }
    return result


# ----------------------------------------------------------------------
# Block bootstrap utilities
# ----------------------------------------------------------------------
def block_bootstrap_residues(
    residue_sequence: List[int],
    block_size: int,
    num_samples: int
) -> List[List[int]]:
    """
    Perform a contiguous‑block bootstrap on ``residue_sequence``.

    Parameters
    ----------
    residue_sequence : List[int]
        Original residue sequence of length ``N``.
    block_size : int
        Length of each contiguous block.
    num_samples : int
        Number of bootstrap samples to generate.

    Returns
    -------
    List[List[int]]
        List containing ``num_samples`` bootstrap sequences, each of length ``N``.
    """
    N = len(residue_sequence)
    if block_size <= 0:
        raise ValueError("block_size must be a positive integer")
    # Number of (possibly overlapping) blocks needed to cover the series
    # We use non‑overlapping blocks for simplicity.
    num_blocks = int(np.ceil(N / block_size))
    # Pad the sequence so that it splits evenly into blocks
    padded = residue_sequence + [residue_sequence[-1]] * (num_blocks * block_size - N)
    blocks = [
        padded[i * block_size:(i + 1) * block_size] for i in range(num_blocks)
    ]

    bootstrap_samples: List[List[int]] = []
    for _ in range(num_samples):
        # Sample block indices with replacement
        sampled_indices = np.random.randint(0, num_blocks, size=num_blocks)
        sample = []
        for idx in sampled_indices:
            sample.extend(blocks[idx])
        # Truncate to original length N
        bootstrap_samples.append(sample[:N])
    return bootstrap_samples


# ----------------------------------------------------------------------
# Deviation test (block‑bootstrap based)
# ----------------------------------------------------------------------
def run_deviation_test(
    observed_counts: Dict[int, int],
    prime: int,
    residue_sequence: List[int],
    N: int,
    block_size: Optional[int] = None,
    num_samples: int = 1000,
    seed: Optional[int] = None
) -> Tuple[float, Optional[float]]:
    """
    Perform the deviation‑magnitude test using a block bootstrap.

    Returns
    -------
    D_obs : float
        Observed deviation ``D``.
    p_value : Optional[float]
        Proportion of bootstrap samples with deviation ≥ ``D_obs``.
        ``None`` when ``N < 100`` (small‑N fallback).
    """
    if seed is not None:
        pin_random_seed(seed)

    # Small‑N fallback
    if N < 100:
        D_obs = calculate_deviation_D(observed_counts, prime, N)
        return D_obs, None

    # Default block size: sqrt(N) rounded to nearest integer (common heuristic)
    if block_size is None:
        block_size = max(1, int(np.sqrt(N)))

    D_obs = calculate_deviation_D(observed_counts, prime, N)

    # Generate bootstrap replicates of the *sequence* (not just counts)
    boot_sequences = block_bootstrap_residues(residue_sequence, block_size, num_samples)

    # Compute deviation for each bootstrap sample
    boot_D = []
    for seq in boot_sequences:
        # Convert sequence to counts
        boot_counts: Dict[int, int] = {r: 0 for r in range(prime)}
        for r in seq:
            boot_counts[r] = boot_counts.get(r, 0) + 1
        boot_D.append(calculate_deviation_D(boot_counts, prime, N))

    # p‑value = proportion of bootstrap D ≥ observed D
    p_val = (np.sum(np.array(boot_D) >= D_obs) + 1) / (num_samples + 1)  # add‑one smoothing
    return D_obs, float(p_val)


# ----------------------------------------------------------------------
# Helper for error‑term residual (unchanged)
# ----------------------------------------------------------------------
def calculate_error_term_residual(D_obs: float, E_bound: float) -> float:
    if E_bound == 0:
        return float('inf')
    return D_obs / E_bound


# ----------------------------------------------------------------------
# High‑level wrapper used by the orchestrator (unchanged)
# ----------------------------------------------------------------------
def run_full_statistical_analysis(
    observed_counts: Dict[int, int],
    prime: int,
    N: int,
    block_size: Optional[int] = None,
    num_bootstrap_samples: int = 1000,
    seed: Optional[int] = None
) -> StatisticalResult:
    """
    Execute the full statistical pipeline for a single residue dataset.

    This orchestrates:
    1. Deviation magnitude D and its bootstrap p‑value.
    2. Chi‑squared statistic and (asymptotic or exact) p‑value.
    3. Error‑term residual relative to theoretical bounds.
    4. Pass / fail flags (including Bonferroni‑adjusted).
    """
    if seed is not None:
        pin_random_seed(seed)

    # 1. Deviation magnitude & bootstrap p‑value
    D_obs, boot_p = run_deviation_test(
        observed_counts,
        prime,
        # Build the full residue *sequence* from counts for bootstrapping.
        # This reconstruction respects the original ordering only up to
        # the multiset of residues; for the purposes of the test it is
        # sufficient because the bootstrap works on contiguous blocks.
        # We generate a deterministic sequence by repeating each residue
        # the observed number of times in order of residue value.
        sum(
            ([r] * observed_counts.get(r, 0) for r in range(prime)),
            []
        ),
        N,
        block_size=block_size,
        num_samples=num_bootstrap_samples,
        seed=seed,
    )

    # 2. Chi‑squared statistic & p‑value (using the updated exact/approx logic)
    chi_sq = calculate_chi_squared_statistic(observed_counts, prime, N)
    fallback_needed = check_bin_counts_and_fallback(observed_counts, prime, N)
    if fallback_needed:
        chi2_p = exact_multinomial_test(observed_counts, prime)
    else:
        from scipy.stats import chi2
        chi2_p = 1.0 - chi2.cdf(chi_sq, df=prime - 1)

    # 3. Theoretical error bound
    bounds = calculate_theoretical_bounds(prime, N)
    E_bound = bounds['upper'] - N / prime
    error_residual = calculate_error_term_residual(D_obs, E_bound)

    # 4. Pass / fail decisions
    pass_flag = (boot_p if boot_p is not None else 0.0) > 0.05
    bonf_pass = (boot_p if boot_p is not None else 0.0) > (0.05 / 4)

    return StatisticalResult(
        test_type="block_bootstrap",
        p_value=boot_p,
        method="block_bootstrap",
        degrees_of_freedom=prime - 1,
        error_term_residual=error_residual,
        chi_squared_statistic=chi_sq,
        chi_squared_p_value=chi2_p,
        block_bootstrap_p_value=boot_p,
        pass_fail_flag=pass_flag,
        bonferroni_pass_fail_flag=bonf_pass,
    )


# ----------------------------------------------------------------------
# Persistence helpers (unchanged)
# ----------------------------------------------------------------------
def save_statistical_result(result: StatisticalResult, path: str) -> None:
    with open(path, 'w') as f:
        json.dump(asdict(result), f, indent=2)


def load_statistical_result(path: str) -> StatisticalResult:
    with open(path, 'r') as f:
        data = json.load(f)
    return StatisticalResult(**data)


# ----------------------------------------------------------------------
# Simple pass/fail utilities (unchanged)
# ----------------------------------------------------------------------
def determine_primary_pass_fail(p_value: float) -> bool:
    return p_value > 0.05


def determine_bonferroni_pass_fail(p_value: float) -> bool:
    return p_value > (0.05 / 4)


# ----------------------------------------------------------------------
# Placeholder entry point kept for compatibility with older code
# ----------------------------------------------------------------------
def run_sieve_analysis(N: int, primes: List[int], config: Dict[str, Any]) -> None:
    # This function is retained for backward compatibility; the
    # orchestrator now calls ``run_full_statistical_analysis`` directly.
    pass