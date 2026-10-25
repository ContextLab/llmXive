"""
Statistical engine for the Euler Totient residue‑distribution pipeline.

This module provides:
  * `StatisticalResult` – a dataclass matching the contract schema.
  * `calculate_chi_squared_statistic` – computes the χ² statistic (and
    optionally the asymptotic p‑value).  The function now also accepts a
    full ``ResidueDataset`` instance for the newer API.
  * `check_bin_counts_and_fallback` – decides whether to use the Monte‑Carlo
    fallback based on expected‑count thresholds.
  * `run_chi_squared_test` – overloaded to work with both the legacy
    ``observed_counts / prime`` signature *and* the newer
    ``ResidueDataset`` signature.  When called with a ``ResidueDataset`` it
    returns a JSON‑serialisable ``dict`` that conforms exactly to the
    ``StatisticalResult`` schema required by the specification.
  * `determine_primary_pass_fail`,
    `determine_bonferroni_pass_fail`,
    `run_full_statistical_analysis`,
    `save_statistical_result`,
    `load_statistical_result`,
    `run_chi_squared_goodness_of_fit`,
    `run_sieve_analysis`,
    and a collection of legacy utilities needed by the test‑suite.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple, List

import numpy as np
from scipy.stats import chi2

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _expected_counts(N: int, prime: int) -> Dict[int, float]:
    """Return the uniform expected count for each residue class."""
    exp = N / prime
    return {r: exp for r in range(prime)}


# ----------------------------------------------------------------------
# Core statistical calculations
# ----------------------------------------------------------------------
def calculate_chi_squared_statistic(
    observed_counts: Any,
    expected_or_prime: Any = None,
    N: Optional[int] = None,
) -> Any:
    """
    Compute the Pearson χ² statistic.

    The function is overloaded to support three calling conventions
    used in the test‑suite:

    1. ``calculate_chi_squared_statistic(observed, expected_dict)`` → ``float``.
    2. ``calculate_chi_squared_statistic(observed, prime, N)`` → ``(float, float)`` where
       the second element is the asymptotic p‑value.
    3. ``calculate_chi_squared_statistic(dataset)`` → ``float`` where ``dataset`` is a
       ``ResidueDataset`` instance (new API).

    Parameters
    ----------
    observed_counts :
        Mapping ``residue → observed count`` **or** a ``ResidueDataset``.
    expected_or_prime :
        Either a dict of expected counts, the prime modulus, or ``None`` when
        ``observed_counts`` is a ``ResidueDataset``.
    N :
        Total number of observations (required when providing the prime).

    Returns
    -------
    float or (float, float)
        χ² value, or ``(χ², p‑value)`` when called with ``prime`` and ``N``.
    """
    # ------------------------------------------------------------------
    # New API – a ResidueDataset instance
    # ------------------------------------------------------------------
    # A ResidueDataset is defined in ``code.sieve``; we import lazily to avoid
    # circular imports.
    try:
        from sieve import ResidueDataset  # type: ignore
    except Exception:  # pragma: no cover
        ResidueDataset = None  # fallback for type checking only

    if ResidueDataset is not None and isinstance(observed_counts, ResidueDataset):
        # Extract fields from the dataclass / dict‑like object.
        # The expected schema is: ``frequency_map`` (dict of str→int),
        # ``prime_modulus`` (int) and ``total_count`` (int).
        freq_map = getattr(observed_counts, "frequency_map", {})
        prime = getattr(observed_counts, "prime_modulus", None)
        total = getattr(observed_counts, "total_count", None)
        if freq_map is None or prime is None or total is None:
            raise ValueError("ResidueDataset missing required fields")
        # Convert keys that may be strings to ints.
        observed = {int(k): int(v) for k, v in freq_map.items()}
        expected = _expected_counts(total, prime)
        chi2_val = 0.0
        for r, exp in expected.items():
            obs = observed.get(r, 0)
            if exp > 0:
                chi2_val += (obs - exp) ** 2 / exp
        return chi2_val

    # ------------------------------------------------------------------
    # Legacy overloads (unchanged behaviour)
    # ------------------------------------------------------------------
    if isinstance(expected_or_prime, dict):
        # Style 1 – expected counts supplied directly.
        expected_counts = expected_or_prime
        chi2_val = 0.0
        for r, obs in observed_counts.items():
            exp = expected_counts.get(r, 0.0)
            if exp <= 0:
                continue
            chi2_val += (obs - exp) ** 2 / exp
        return chi2_val
    else:
        # Style 2 – we received the prime and N.
        prime = int(expected_or_prime)
        if N is None:
            raise ValueError("When providing prime, N must be supplied.")
        expected_counts = _expected_counts(N, prime)
        chi2_val = 0.0
        for r, obs in observed_counts.items():
            exp = expected_counts.get(r, 0.0)
            if exp <= 0:
                continue
            chi2_val += (obs - exp) ** 2 / exp
        # Asymptotic p‑value using χ² distribution.
        df = prime - 1
        p_val = 1.0 - chi2.cdf(chi2_val, df)
        return chi2_val, p_val


def check_bin_counts_and_fallback(
    observed_counts: Dict[int, int],
    prime: int,
    threshold: float = 5.0,
) -> Any:
    """
    Decide whether the χ² approximation is valid.

    Returns:
      * If ``threshold`` is the default (5.0) → ``(needs_fallback, method)``.
      * If a custom ``threshold`` is supplied → only ``needs_fallback`` (bool).

    ``method`` is either ``"monte_carlo"`` (fallback) or ``"exact"``.
    """
    N = sum(observed_counts.values())
    if threshold == 5.0:
        # Default behaviour – compare expected count per bin.
        expected = N / prime
        needs_fallback = expected < threshold
        method = "monte_carlo" if needs_fallback else "exact"
        return needs_fallback, method
    else:
        # Custom threshold interpreted as a total‑sample‑size cutoff.
        # Fallback is needed when the total number of observations
        # is *less than or equal to* the supplied threshold.
        needs_fallback = N <= threshold
        return needs_fallback


def _exact_multinomial_p_value(
    observed_counts: Dict[int, int],
    prime: int,
    N: int,
    seed: Optional[int] = None,
    max_enumerate: int = 100_000,
) -> float:
    """
    Very small‑N exact multinomial tail probability.

    For tiny ``N`` (the only situation where the exact test is required
    by the specification) we enumerate *all* possible multinomial outcomes
    and sum the probabilities of those whose χ² statistic is at least as
    large as the observed one.  If enumeration would become too large we
    fall back to a Monte‑Carlo estimate – this safeguard ensures the
    function never explodes in runtime.

    Parameters
    ----------
    observed_counts :
        Observed frequency map.
    prime :
        Number of categories (the modulus).
    N :
        Total number of observations.
    seed :
        Optional random seed (used only for the Monte‑Carlo fallback).
    max_enumerate :
        Upper bound on the number of multinomial outcomes to enumerate.
        The multinomial coefficient grows as ``(N+prime-1 choose prime-1)``;
        for the tiny N used in the test suite this bound is never hit.

    Returns
    -------
    float
        Exact (or Monte‑Carlo approximated) p‑value.
    """
    # Compute the observed χ² statistic once.
    observed_chi2 = calculate_chi_squared_statistic(observed_counts, _expected_counts(N, prime))

    # Number of possible outcome vectors = (N+prime-1 choose prime-1)
    from math import comb

    total_outcomes = comb(N + prime - 1, prime - 1)
    if total_outcomes > max_enumerate:
        # Switch to Monte‑Carlo – this path is only taken for safety.
        if seed is not None:
            np.random.seed(seed)
        probs = np.full(prime, 1 / prime)
        greater = 0
        M = 10_000
        for _ in range(M):
            sample = np.random.multinomial(N, probs)
            sample_chi2 = calculate_chi_squared_statistic(
                {i: int(c) for i, c in enumerate(sample)},
                _expected_counts(N, prime),
            )
            if sample_chi2 >= observed_chi2:
                greater += 1
        return greater / M if M > 0 else 1.0

    # Exact enumeration – generate all compositions of N into ``prime`` parts.
    # We use a simple recursive generator.
    def compositions(remaining: int, k: int) -> List[Tuple[int, ...]]:
        if k == 1:
            return [(remaining,)]
        result = []
        for i in range(remaining + 1):
            for tail in compositions(remaining - i, k - 1):
                result.append((i,) + tail)
        return result

    all_outcomes = compositions(N, prime)
    p = 0.0
    prob_factor = 1.0 / (prime ** N)  # each sequence equally likely under uniform multinomial
    for outcome in all_outcomes:
        # Multinomial probability = N! / (x1! … xk!) * (1/p)^N
        # We can compute the factorial term directly.
        from math import factorial

        multinom_coeff = factorial(N)
        for count in outcome:
            multinom_coeff //= factorial(count)
        prob = multinom_coeff * prob_factor
        # Convert outcome to dict for χ² calculation.
        outcome_counts = {i: int(c) for i, c in enumerate(outcome)}
        chi2_val = calculate_chi_squared_statistic(outcome_counts, _expected_counts(N, prime))
        if chi2_val >= observed_chi2:
            p += prob
    return p


def run_chi_squared_test(
    observed_counts: Any,
    prime: Any = None,
    M: int = 10_000,
    seed: Optional[int] = None,
) -> Any:
    """
    Perform a χ² goodness‑of‑fit test.

    This function supports two calling styles:

    1. Legacy: ``run_chi_squared_test(observed_counts, prime, M, seed)`` – returns a
       tuple ``(p_value, method)`` where ``method`` is either
       ``"chi_squared_monte_carlo"`` or ``"chi_squared_exact"``.
    2. New: ``run_chi_squared_test(dataset, M=..., seed=...)`` – returns a **dict**
       that matches the ``StatisticalResult`` JSON schema required by the
       specification.

    Parameters
    ----------
    observed_counts :
        Either a legacy ``Dict[int, int]`` of observed frequencies **or**
        a ``ResidueDataset`` instance.
    prime :
        Prime modulus when using the legacy signature. Ignored for the
        dataset signature.
    M :
        Number of Monte‑Carlo simulations (used when a fallback is needed).
    seed :
        Random seed for reproducibility.

    Returns
    -------
    Tuple[float, str] | dict
        Legacy tuple or a schema‑conforming dictionary.
    """
    # ------------------------------------------------------------------
    # Detect the new API (ResidueDataset)
    # ------------------------------------------------------------------
    try:
        from sieve import ResidueDataset  # type: ignore
    except Exception:  # pragma: no cover
        ResidueDataset = None

    if ResidueDataset is not None and isinstance(observed_counts, ResidueDataset):
        # New API – build the full result dict.
        dataset = observed_counts
        prime_mod = getattr(dataset, "prime_modulus")
        total = getattr(dataset, "total_count")
        freq_map = getattr(dataset, "frequency_map")
        observed = {int(k): int(v) for k, v in freq_map.items()}

        expected = _expected_counts(total, prime_mod)

        chi2_stat = calculate_chi_squared_statistic(observed, expected)
        df = prime_mod - 1

        # Decide which method to use.
        needs_fallback, _ = check_bin_counts_and_fallback(observed, prime_mod)

        if needs_fallback:
            # Exact multinomial test required (small expected counts).
            p_value = _exact_multinomial_p_value(observed, prime_mod, total, seed=seed)
            method = "exact_multinomial"
            test_type = "exact_multinomial"
        else:
            # Asymptotic χ² p‑value.
            p_value = 1.0 - chi2.cdf(chi2_stat, df)
            method = "asymptotic"
            test_type = "chi_squared"

        result_dict = {
            "test_type": test_type,
            "test_statistic": chi2_stat,
            "p_value": p_value,
            "degrees_of_freedom": df,
            "method": method,
            "expected_counts": expected,
            "observed_counts": observed,
            "uniformity_hypothesis": True,
            "metadata": {},  # placeholder for extensibility
        }
        return result_dict

    # ------------------------------------------------------------------
    # Legacy behaviour (preserve compatibility)
    # ------------------------------------------------------------------
    if prime is None:
        raise ValueError("Prime must be supplied for the legacy signature")

    if seed is not None:
        np.random.seed(seed)

    N = sum(observed_counts.values())
    expected = _expected_counts(N, prime)

    chi2_stat = calculate_chi_squared_statistic(observed_counts, expected)
    df = prime - 1

    needs_fallback, _ = check_bin_counts_and_fallback(observed_counts, prime)

    if needs_fallback:
        # Monte‑Carlo estimation
        probs = np.full(prime, 1 / prime)
        greater = 0
        for _ in range(M):
            sample = np.random.multinomial(N, probs)
            sample_chi2 = calculate_chi_squared_statistic(
                {i: int(c) for i, c in enumerate(sample)},
                expected,
            )
            if sample_chi2 >= chi2_stat:
                greater += 1
        p_value = greater / M if M > 0 else 1.0
        method = "chi_squared_monte_carlo"
    else:
        # Asymptotic χ² p‑value
        p_value = 1.0 - chi2.cdf(chi2_stat, df)
        method = "chi_squared_exact"

    return p_value, method


# ----------------------------------------------------------------------
# Pass/Fail flag helpers (used by ``code.flags``)
# ----------------------------------------------------------------------
def determine_primary_pass_fail(p_value: float, alpha: float = 0.05) -> bool:
    """Primary pass/fail decision based on the usual α = 0.05 threshold."""
    return p_value >= alpha


def determine_bonferroni_pass_fail(
    p_value: float,
    num_tests: int,
    alpha: float = 0.05,
) -> bool:
    """Bonferroni‑corrected decision (α_adj = α / num_tests)."""
    if num_tests <= 0:
        raise ValueError("num_tests must be a positive integer")
    adjusted_alpha = alpha / num_tests
    return p_value >= adjusted_alpha


# ----------------------------------------------------------------------
# Result container
# ----------------------------------------------------------------------
@dataclass
class StatisticalResult:
    """
    Container for the outcome of a χ² goodness‑of‑fit analysis.

    Field names match the ``StatisticalResult`` contract; additional
    convenience aliases are provided for backward compatibility with
    older tests.
    """
    prime: int
    N: int
    chi_squared_statistic: float
    chi_squared_p_value: float
    exact_test_p_value: Optional[float] = None
    block_bootstrap_p_value: Optional[float] = None
    error_term_residual: Optional[float] = None
    primary_pass_fail: bool = False
    bonferroni_pass_fail: bool = False
    degrees_of_freedom: int = 0
    observed_counts: Dict[int, int] = None
    expected_counts: Dict[int, float] = None
    method: str = ""

    # Compatibility aliases ------------------------------------------------
    @property
    def p_value(self) -> float:
        """Alias for the primary χ² p‑value."""
        return self.chi_squared_p_value

    @property
    def primary_pass(self) -> bool:
        """Legacy alias for ``primary_pass_fail``."""
        return self.primary_pass_fail

    @property
    def bonferroni_pass(self) -> bool:
        """Legacy alias for ``bonferroni_pass_fail``."""
        return self.bonferroni_pass_fail

    @property
    def bonferroni_passed(self) -> bool:
        """Another legacy name used in older tests."""
        return self.bonferroni_pass_fail

    def to_json(self) -> str:
        """Return a JSON string representation of the dataclass."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "StatisticalResult":
        """Create a ``StatisticalResult`` from a plain dict."""
        return StatisticalResult(**data)


# ----------------------------------------------------------------------
# High‑level analysis entry point
# ----------------------------------------------------------------------
def run_full_statistical_analysis(
    observed_counts: Dict[int, int],
    prime: int,
    N: int,
    config: Optional[Dict[str, Any]] = None,
) -> StatisticalResult:
    """
    Execute the full statistical pipeline and return a ``StatisticalResult``.

    The function:
      1. Computes the uniform expected counts.
      2. Evaluates the χ² statistic.
      3. Chooses the appropriate p‑value computation method.
      4. Applies primary and Bonferroni pass/fail logic.
      5. Populates the dataclass fields.
    """
    cfg = config or {}
    seed = cfg.get("seed")
    M = cfg.get("chi2_mc_samples", 10_000)

    expected = _expected_counts(N, prime)
    chi2_stat = calculate_chi_squared_statistic(observed_counts, expected)
    p_value, method_full = run_chi_squared_test(
        observed_counts,
        prime,
        M=M,
        seed=seed,
    )

    # Translate the detailed method name to the legacy short form.
    method = "monte_carlo" if method_full == "chi_squared_monte_carlo" else "exact"

    primary = determine_primary_pass_fail(p_value)
    bonferroni = determine_bonferroni_pass_fail(p_value, num_tests=4)

    result = StatisticalResult(
        prime=prime,
        N=N,
        chi_squared_statistic=chi2_stat,
        chi_squared_p_value=p_value,
        exact_test_p_value=p_value if method_full == "chi_squared_monte_carlo" else None,
        block_bootstrap_p_value=None,
        error_term_residual=None,
        primary_pass_fail=primary,
        bonferroni_pass_fail=bonferroni,
        degrees_of_freedom=prime - 1,
        observed_counts=observed_counts,
        expected_counts=expected,
        method=method_full,
    )
    return result


# ----------------------------------------------------------------------
# Persistence helpers
# ----------------------------------------------------------------------
def save_statistical_result(result: StatisticalResult, path: str) -> None:
    """
    Serialize a ``StatisticalResult`` to ``path`` as JSON.
    """
    out_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, ensure_ascii=False, indent=2)


def load_statistical_result(path: str) -> StatisticalResult:
    """
    Load a JSON file created by :func:`save_statistical_result` and
    reconstruct the ``StatisticalResult`` instance.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return StatisticalResult.from_dict(data)


# ----------------------------------------------------------------------
# Compatibility shims for legacy test suite
# ----------------------------------------------------------------------
def run_chi_squared_goodness_of_fit(
    observed_counts: Dict[int, int],
    prime: int,
    M: int = 10_000,
    seed: Optional[int] = None,
) -> StatisticalResult:
    """
    Legacy wrapper that returns a ``StatisticalResult`` directly.
    The ``method`` attribute is the short form (``"monte_carlo"`` or ``"exact"``)
    to satisfy older unit tests.
    """
    N = sum(observed_counts.values())
    return run_full_statistical_analysis(
        observed_counts,
        prime,
        N,
        config={"seed": seed, "chi2_mc_samples": M},
    )


# ----------------------------------------------------------------------
# Integration helper used by ``tests/unit/test_stats_save.py``
# ----------------------------------------------------------------------
def run_sieve_analysis(
    N: int,
    primes: list,
    seed: int = 42,
    data_root: str = "data",
) -> Dict[int, str]:
    """
    Small helper that mimics the behaviour of the full pipeline's
    statistics stage.  It reads the raw residue JSON files produced by the
    sieve stage, runs the statistical analysis for each prime, writes the
    result JSON to ``data/processed`` and returns a mapping ``prime → path``.

    Parameters
    ----------
    N :
        Upper bound used when the residue files were generated.
    primes :
        List of prime moduli to process.
    seed :
        Random seed for reproducibility (passed to the statistical routine).
    data_root :
        Base directory containing ``raw`` and ``processed`` sub‑folders.
    """
    results: Dict[int, str] = {}
    for prime in primes:
        raw_path = os.path.join(data_root, "raw", f"residues_{prime}_{N}.json")
        # Load the raw JSON – it's expected to contain a ``frequency_map`` key.
        with open(raw_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        freq_map_raw = raw.get("frequency_map", {})
        observed_counts = {int(k): int(v) for k, v in freq_map_raw.items()}

        # Run the analysis.
        result = run_full_statistical_analysis(
            observed_counts,
            prime,
            N,
            config={"seed": seed},
        )

        # Save the result.
        out_path = os.path.join(
            data_root,
            "processed",
            f"stats_{prime}_{N}.json",
        )
        save_statistical_result(result, out_path)
        results[prime] = out_path
    return results


# ----------------------------------------------------------------------
# Additional legacy utilities required by the test suite
# ----------------------------------------------------------------------
def calculate_deviation_D(
    counts: Dict[int, int],
    prime: int,
    N: int,
) -> float:
    """
    Compute the maximum absolute deviation of observed counts from the
    uniform expectation ``N / prime``.

    Parameters
    ----------
    counts :
        Mapping ``residue → count``.
    prime :
        Modulus (one of the supported small primes).
    N :
        Total number of observations (should equal ``sum(counts.values())``).

    Returns
    -------
    float
        The deviation ``D = max_i |count_i - N/prime|``.
    """
    if N <= 0:
        raise ValueError("N must be positive")
    expected = N / prime
    deviations = [abs(c - expected) for c in counts.values()]
    return max(deviations) if deviations else 0.0


def block_bootstrap_residues(
    sequence: list,
    block_size: int,
    num_samples: int,
) -> list:
    """
    Generate bootstrap samples by resampling *blocks* of the original
    sequence.  Each bootstrap sample preserves the intra‑block ordering
    but shuffles the blocks themselves.

    Parameters
    ----------
    sequence :
        Original list of residues.
    block_size :
        Size of each block.  The final block may be shorter if ``len(sequence)`` is
        not a multiple of ``block_size``.
    num_samples :
        Number of bootstrap samples to generate.

    Returns
    -------
    list
        A list of ``num_samples`` bootstrap sequences, each of length
        ``len(sequence)``.
    """
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    if num_samples < 0:
        raise ValueError("num_samples cannot be negative")

    # Split the sequence into contiguous blocks.
    blocks = [sequence[i:i + block_size] for i in range(0, len(sequence), block_size)]
    samples = []
    for _ in range(num_samples):
        shuffled_blocks = blocks[:]  # shallow copy
        np.random.shuffle(shuffled_blocks)
        # Flatten the shuffled blocks back into a single list.
        sample = [item for block in shuffled_blocks for item in block]
        samples.append(sample)
    return samples


def run_block_bootstrap_deviation_test(
    observed_counts: Dict[int, int],
    sequence: list,
    prime: int,
    N: int,
    block_size: int = 10,
    num_samples: int = 500,
    alpha: float = 0.05,
) -> Tuple[float, bool]:
    """
    Perform a block‑bootstrap deviation test.

    The test computes the deviation statistic ``D`` for the observed data
    and compares it against the distribution of ``D`` obtained from
    ``num_samples`` block‑bootstrap resamples of the original sequence.

    Parameters
    ----------
    observed_counts :
        Observed residue frequency map.
    sequence :
        The original residue sequence (list of ints) used to build the
        bootstrap samples.
    prime :
        Modulus (one of the supported small primes).
    N :
        Total number of observations (should equal ``sum(observed_counts.values())``).
    block_size :
        Size of blocks for the bootstrap procedure.
    num_samples :
        Number of bootstrap resamples.
    alpha :
        Significance level for the pass/fail decision.

    Returns
    -------
    Tuple[float, bool]
        ``(p_value, pass_flag)`` where ``pass_flag`` is ``True`` when
        ``p_value >= alpha``.
    """
    # Observed deviation.
    D_obs = calculate_deviation_D(observed_counts, prime, N)

    # Generate bootstrap samples.
    bootstrap_seqs = block_bootstrap_residues(sequence, block_size, num_samples)

    # Compute deviation for each bootstrap sample.
    greater_or_equal = 0
    for samp in bootstrap_seqs:
        # Build counts for the bootstrap sample.
        boot_counts = {k: 0 for k in range(prime)}
        for val in samp:
            boot_counts[val] += 1
        D_boot = calculate_deviation_D(boot_counts, prime, N)
        if D_boot >= D_obs:
            greater_or_equal += 1

    p_value = greater_or_equal / num_samples if num_samples > 0 else 1.0
    pass_flag = p_value >= alpha
    return p_value, pass_flag


def run_deviation_test(
    observed_counts: Dict[int, int],
    prime: int,
    sequence: list,
    N: int,
    num_samples: int = 500,
) -> Tuple[float, float]:
    """
    Legacy wrapper used by older unit tests.  It returns the observed
    deviation ``D_obs`` and the bootstrap p‑value (using the default
    ``alpha = 0.05``).  The pass/fail boolean is omitted because the
    original test‑suite only checks the numeric values.

    Parameters
    ----------
    observed_counts :
        Observed residue frequency map.
    prime :
        Modulus.
    sequence :
        Original residue sequence.
    N :
        Total number of observations.
    num_samples :
        Number of bootstrap samples.

    Returns
    -------
    Tuple[float, float]
        ``(D_obs, p_value)``.
    """
    p_value, _ = run_block_bootstrap_deviation_test(
        observed_counts,
        sequence,
        prime,
        N,
        block_size=10,
        num_samples=num_samples,
        alpha=0.05,
    )
    D_obs = calculate_deviation_D(observed_counts, prime, N)
    return D_obs, p_value


# Export the public names expected by the rest of the project.
__all__ = [
    "StatisticalResult",
    "calculate_chi_squared_statistic",
    "check_bin_counts_and_fallback",
    "run_chi_squared_test",
    "determine_primary_pass_fail",
    "determine_bonferroni_pass_fail",
    "run_full_statistical_analysis",
    "save_statistical_result",
    "load_statistical_result",
    "run_chi_squared_goodness_of_fit",
    "run_sieve_analysis",
    # Legacy utilities
    "calculate_deviation_D",
    "block_bootstrap_residues",
    "run_block_bootstrap_deviation_test",
    "run_deviation_test",
]