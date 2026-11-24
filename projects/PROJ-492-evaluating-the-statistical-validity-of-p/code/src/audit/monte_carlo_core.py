"""
Monte‑Carlo core utilities for validating statistical test implementations
(FR‑026).

This module provides a lightweight, deterministic Monte‑Carlo harness that
generates synthetic data under the null hypothesis for the four statistical
tests used throughout the audit pipeline:

* Two‑proportion Z‑test
* Fisher’s exact test
* Welch’s two‑sample t‑test
* Binomial test

The public API mirrors the imports used by
``code/src/audit/monte_carlo_validation.py``:

* ``set_seeds(seed: int)`` – set the global RNG seeds.
* ``simulate_z_test_statistic(n1, n2, p)`` – draw a contingency table under
  the null hypothesis (equal proportions) and return the Z‑statistic.
* ``simulate_fisher_exact_table(n1, n2, x1, x2)`` – generate a random
  2 × 2 table with the same margins as the observed table and return the
  two‑sided Fisher exact p‑value.
* ``simulate_welch_t_statistic(n1, n2, mean1, mean2, std1, std2)`` – draw
  two independent normal samples and return the Welch t‑statistic.
* ``simulate_binomial_statistic(n, p, k)`` – draw a binomial count under the
  null and return the two‑sided binomial test p‑value.
* ``run_monte_carlo_validation_core(simulate_func, num_replicates, alpha)`` –
  orchestrates the simulation, computes an empirical p‑value, and returns a
  tuple ``(empirical_p, observed_value)``.  The function distinguishes
  between statistic‑based simulations (Z, t) and p‑value‑based simulations
  (Fisher, binomial) automatically.
"""

from __future__ import annotations

import random
from typing import Callable, Tuple

import numpy as np
from scipy import stats

# ----------------------------------------------------------------------
# Seed handling
# ----------------------------------------------------------------------
def set_seeds(seed: int) -> None:
    """
    Set deterministic seeds for the Python ``random`` module and NumPy.

    Parameters
    ----------
    seed: int
        The seed value to use for all RNGs.
    """
    random.seed(seed)
    np.random.seed(seed)

# ----------------------------------------------------------------------
# Simulation helpers
# ----------------------------------------------------------------------
def simulate_z_test_statistic(n1: int, n2: int, p: float) -> float:
    """
    Simulate a two‑proportion Z‑test statistic under the null hypothesis
    that the two proportions are equal to ``p``.

    Returns
    -------
    float
        The Z‑statistic (signed).
    """
    # Generate counts under the null
    x1 = np.random.binomial(n1, p)
    x2 = np.random.binomial(n2, p)

    # Pooled proportion
    pooled = (x1 + x2) / (n1 + n2)

    # Standard error; guard against zero
    se = np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        se = 1e-12

    # Z‑statistic (difference of sample proportions)
    z = (x1 / n1 - x2 / n2) / se
    return z

def simulate_fisher_exact_table(n1: int, n2: int, x1: int, x2: int) -> float:
    """
    Simulate a 2 × 2 contingency table with the same margins as the observed
    table and return the two‑sided Fisher exact p‑value.

    Parameters
    ----------
    n1, n2 : int
        Row totals (sample sizes of the two groups).
    x1, x2 : int
        Observed successes in each group (used only to obtain the total
        number of successes).

    Returns
    -------
    float
        Two‑sided Fisher exact p‑value for the simulated table.
    """
    total_successes = x1 + x2
    total = n1 + n2

    # Hypergeometric draw for the first row's successes
    # M = total population, n = total_successes, N = n1 draws
    x1_prime = stats.hypergeom.rvs(M=total, n=total_successes, N=n1)

    # Derive the remaining cell counts
    x2_prime = total_successes - x1_prime
    table = [[int(x1_prime), int(n1 - x1_prime)],
             [int(x2_prime), int(n2 - x2_prime)]]

    _, p_val = stats.fisher_exact(table, alternative="two-sided")
    return p_val

def simulate_welch_t_statistic(
    n1: int,
    n2: int,
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
) -> float:
    """
    Simulate two independent normal samples and return the Welch t‑statistic.

    Returns
    -------
    float
        The t‑statistic (signed).
    """
    sample1 = np.random.normal(loc=mean1, scale=std1, size=n1)
    sample2 = np.random.normal(loc=mean2, scale=std2, size=n2)

    t_stat, _ = stats.ttest_ind(sample1, sample2, equal_var=False)
    return t_stat

def simulate_binomial_statistic(n: int, p: float, k: int) -> float:
    """
    Simulate a binomial count under the null hypothesis and return the
    two‑sided binomial test p‑value.

    Parameters
    ----------
    n : int
        Number of trials.
    p : float
        Success probability under the null.
    k : int
        Observed number of successes (used only to compute the observed
        p‑value; the simulated count is drawn anew).

    Returns
    -------
    float
        Two‑sided binomial test p‑value for the simulated count.
    """
    k_sim = np.random.binomial(n, p)
    # ``stats.binom_test`` is deprecated but still available in the
    # execution environment and matches the signature used elsewhere.
    p_val = stats.binom_test(k_sim, n, p, alternative="two-sided")
    return p_val

# ----------------------------------------------------------------------
# Core orchestration
# ----------------------------------------------------------------------
def run_monte_carlo_validation_core(
    simulate_func: Callable[[], float],
    num_replicates: int,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    """
    Run a Monte‑Carlo validation loop.

    The first call to ``simulate_func`` yields the *observed* value.
    Subsequent calls generate the null distribution.  The empirical
    p‑value is computed as the proportion of simulated values that are at
    least as extreme as the observed value.  For statistic‑based
    simulations (Z, t) we use a two‑sided absolute‑value comparison.
    For p‑value‑based simulations (Fisher, binomial) we treat smaller
    values as more extreme.

    Parameters
    ----------
    simulate_func : Callable[[], float]
        Function that returns either a test statistic or a p‑value.
    num_replicates : int
        Total number of Monte‑Carlo replicates (including the observed
        draw).  Must be ≥ 2.
    alpha : float, optional
        Unused in the current implementation but kept for API compatibility
        with earlier versions of the pipeline.

    Returns
    -------
    Tuple[float, float]
        ``(empirical_p, observed_value)`` where ``empirical_p`` is the
        Monte‑Carlo estimate of the p‑value and ``observed_value`` is the
        statistic (or p‑value) generated from the first draw.
    """
    if num_replicates < 2:
        raise ValueError("num_replicates must be at least 2")

    # Observed value – first draw
    observed = simulate_func()

    # Generate the remaining replicates
    simulated = [simulate_func() for _ in range(num_replicates - 1)]

    # Decide whether we are dealing with a statistic or a p‑value.
    # Heuristic: if the observed value lies in [0, 1] it is likely a p‑value.
    if 0.0 <= observed <= 1.0:
        # Smaller p‑values are more extreme.
        extreme_count = sum(1 for v in simulated if v <= observed)
    else:
        # For statistics we use a two‑sided absolute‑value comparison.
        extreme_count = sum(1 for v in simulated if abs(v) >= abs(observed))

    empirical_p = extreme_count / num_replicates
    return empirical_p, observed

# ----------------------------------------------------------------------
# Backwards‑compatible wrapper (kept for import safety)
# ----------------------------------------------------------------------
def compute_empirical_p_value(*, observed: float, simulated: list[float]) -> float:
    """
    Legacy helper retained for compatibility with older pipeline code.
    It computes the empirical p‑value using the same logic as
    ``run_monte_carlo_validation_core`` but expects the caller to provide
    the simulated values explicitly.

    Parameters
    ----------
    observed : float
        Observed statistic or p‑value.
    simulated : list[float]
        List of simulated statistics/p‑values.

    Returns
    -------
    float
        Empirical p‑value.
    """
    if 0.0 <= observed <= 1.0:
        extreme = sum(1 for v in simulated if v <= observed)
    else:
        extreme = sum(1 for v in simulated if abs(v) >= abs(observed))
    return extreme / (len(simulated) + 1)  # +1 accounts for the observed draw
