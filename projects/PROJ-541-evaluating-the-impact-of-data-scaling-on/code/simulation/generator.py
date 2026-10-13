"""
Synthetic data generator for simulation (FR-001).
Generates two-group data with controlled distributional properties
(mean difference, variance, skewness) where the ground truth for the
null and alternative hypotheses is explicitly known.

Implementation notes
--------------------
* Skewness is realized with the Pearson type III distribution
  (``scipy.stats.pearson3``), whose population skewness equals its
  single shape parameter, so a requested skewness of 2.0 yields a
  sample skewness within +/- 0.1 for moderate n.
* Each group is generated independently and then re-centered on its
  target location (subtracting the sample mean and adding the target).
  This pins the realized mean difference exactly to the requested
  effect size (0 for the null, ``effect_size`` for the alternative)
  without altering variance or skewness.
* Kurtosis is accepted for API compatibility; under Pearson III the
  kurtosis is a deterministic function of the skewness, so it cannot
  be controlled independently. This is documented, not silently ignored.
"""

import logging
from typing import Optional, Tuple

import numpy as np
from scipy import stats

from simulation.config import SimulationConfig
from simulation.logger import setup_logger

logger = setup_logger(__name__)

__all__ = [
    "generate_null",
    "generate_alternative",
    "generate_synthetic_data",
    "generate_synthetic_data_from_config",
]


def _draw_centered(
    n: int,
    variance: float,
    skewness: float,
    rng: np.random.Generator,
    target_mean: float = 0.0,
) -> np.ndarray:
    """
    Draw ``n`` samples with the requested variance/skewness, then
    re-center the sample so its empirical mean equals ``target_mean``.

    Re-centering (subtracting a constant) leaves variance and skewness
    unchanged, so the distributional shape is preserved while the
    realized mean is pinned exactly.
    """
    if variance < 1e-9:
        # Edge case from the spec: zero variance must be surfaced, not
        # silently produce NaNs downstream.
        logger.log(
            "WARNING",
            message="Skipping iteration: zero variance detected",
        )
        return np.array([], dtype=float)

    scale = float(np.sqrt(variance))
    if abs(skewness) < 1e-6:
        base = rng.normal(loc=0.0, scale=scale, size=n)
    else:
        # Pearson type III: population skewness == shape parameter.
        base = stats.pearson3.rvs(
            skew=skewness, loc=0.0, scale=scale, size=n, random_state=rng
        )

    # Pin the empirical mean to the target location.
    return base - base.mean() + target_mean


def generate_null(
    n_samples: int = 1000,
    variance: float = 1.0,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a two-group dataset under the NULL hypothesis
    (true mean difference = 0).

    Args:
        n_samples: Number of samples per group.
        variance: Target variance of each group.
        skewness: Target skewness (0 -> normal).
        kurtosis: Accepted for API compatibility (see module docstring).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (group1, group2) numpy arrays. The realized mean
        difference is exactly 0.
    """
    if n_samples <= 0:
        raise ValueError(f"n_samples must be positive, got {n_samples}")
    if variance < 0:
        raise ValueError(f"variance must be non-negative, got {variance}")

    rng = np.random.default_rng(seed)
    group1 = _draw_centered(n_samples, variance, skewness, rng, 0.0)
    group2 = _draw_centered(n_samples, variance, skewness, rng, 0.0)
    return group1, group2


def generate_alternative(
    effect_size: float = 1.0,
    n_samples: int = 1000,
    variance: float = 1.0,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a two-group dataset under the ALTERNATIVE hypothesis
    (true mean difference = ``effect_size``).

    Args:
        effect_size: True mean difference (group2 mean - group1 mean).
        n_samples: Number of samples per group.
        variance: Target variance of each group.
        skewness: Target skewness (0 -> normal).
        kurtosis: Accepted for API compatibility (see module docstring).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (group1, group2) numpy arrays. The realized mean
        difference is exactly ``effect_size``.
    """
    if n_samples <= 0:
        raise ValueError(f"n_samples must be positive, got {n_samples}")
    if variance < 0:
        raise ValueError(f"variance must be non-negative, got {variance}")

    rng = np.random.default_rng(seed)
    group1 = _draw_centered(n_samples, variance, skewness, rng, 0.0)
    group2 = _draw_centered(n_samples, variance, skewness, rng, float(effect_size))
    return group1, group2


def generate_synthetic_data(
    mean: float,
    var: float,
    skew: float,
    kurt: float,
    n: int,
    seed: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic data with specified moments (legacy API).

    Args:
        mean: Target mean difference (group2 mean - group1 mean).
        var: Variance.
        skew: Skewness.
        kurt: Kurtosis (accepted; see module docstring).
        n: Number of samples per group.
        seed: Random seed.

    Returns:
        Tuple of (group1, group2) numpy arrays. Empty arrays are
        returned when ``var`` is (numerically) zero, matching the
    edge-case behavior expected by the simulation driver.
    """
    if var < 1e-9:
        logger.log("WARNING", message="Skipping iteration: zero variance detected")
        return np.array([]), np.array([])

    return generate_alternative(
        effect_size=mean,
        n_samples=n,
        variance=var,
        skewness=skew,
        kurtosis=kurt,
        seed=seed,
    )


def generate_synthetic_data_from_config(
    config: SimulationConfig,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic data based on a simulation config.

    Args:
        config: SimulationConfig object.

    Returns:
        Tuple of (group1, group2) numpy arrays.
    """
    return generate_synthetic_data(
        mean=config.mean_diff,
        var=config.variance,
        skew=config.skewness,
        kurt=config.kurtosis,
        n=config.n_samples,
        seed=config.seed,
    )
