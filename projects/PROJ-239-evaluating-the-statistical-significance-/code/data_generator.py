"""
Data generator module for simulating A/B test results with intra‑cluster correlation.

This module implements a random‑intercept model to generate synthetic data that
exhibits intra‑cluster correlation (ICC). The model is defined as:

    Y_ij = μ + u_i + ε_ij

where:
    - Y_ij is the outcome for observation j in cluster i.
    - μ is the global mean (set to 0 for simplicity).
    - u_i is the random intercept for cluster i, u_i ~ N(0, σ_b²).
    - ε_ij is the individual error term, ε_ij ~ N(0, σ_w²).

The Intraclass Correlation Coefficient (ICC) is defined as:
    ICC = σ_b² / (σ_b² + σ_w²)

This generator:
    * Draws cluster sizes from a log‑normal distribution (unless explicit sizes are provided).
    * Generates outcomes with a target ICC.
    * Assigns treatment at the cluster level (50 % treated, 50 % control).
    * Handles the edge case ICC = 0 (independent observations) and warns on highly
      unbalanced cluster sizes.

The function is used by the simulation runner and unit tests. It accepts optional
``cluster_mean`` and ``cluster_std`` arguments – if supplied, they control the
log‑normal distribution used to generate unbalanced cluster sizes.
"""
import warnings
from typing import List, Union, Optional

import numpy as np
import pandas as pd

from code.config import set_seed, CLUSTER_MEAN_SIZE, CLUSTER_STD_SIZE

def _lognormal_params(mean: float, std: float) -> tuple:
    """
    Convert a desired arithmetic mean and standard deviation to the parameters
    of the underlying normal distribution for ``np.random.lognormal``.

    Returns:
        (mu, sigma) – the mean and standard deviation of the *log* of the variable.
    """
    # Guard against non‑positive inputs which would make the log undefined.
    if mean <= 0:
        raise ValueError("Log‑normal mean must be positive.")
    if std <= 0:
        raise ValueError("Log‑normal std must be positive.")

    sigma_sq = np.log(1 + (std / mean) ** 2)
    sigma = np.sqrt(sigma_sq)
    mu = np.log(mean) - sigma_sq / 2
    return mu, sigma

def generate_data(
    n_clusters: int,
    n_obs_per_cluster: Union[int, List[int], None] = None,
    icc: float = 0.0,
    seed: int = 42,
    treatment_effect: float = 0.0,
    cluster_mean: Optional[float] = None,
    cluster_std: Optional[float] = None,
) -> pd.DataFrame:
    """
    Generate synthetic A/B‑test data with cluster‑level correlation.

    Parameters
    ----------
    n_clusters : int
        Number of clusters to generate. Must be >= 50 unless ``icc == 0.0``.
    n_obs_per_cluster : int, list[int] or None
        * If ``int`` – all clusters have this fixed size.
        * If ``list[int]`` – must have length ``n_clusters``; each entry gives the
          size of the corresponding cluster.
        * If ``None`` – cluster sizes are drawn from a log‑normal distribution.
          The distribution’s mean and standard deviation are taken from
          ``cluster_mean``/``cluster_std`` if provided, otherwise from the
          defaults defined in ``code.config``.
    icc : float, default 0.0
        Target intra‑cluster correlation (0.0 ≤ icc ≤ 1.0).
    seed : int, default 42
        Random seed for reproducibility.
    treatment_effect : float, default 0.0
        Difference in means between treatment and control (0.0 for Type I error
        simulations).
    cluster_mean : float, optional
        Desired arithmetic mean of the log‑normal cluster‑size distribution.
        Ignored if ``n_obs_per_cluster`` is supplied.
    cluster_std : float, optional
        Desired arithmetic standard deviation of the log‑normal cluster‑size
        distribution. Ignored if ``n_obs_per_cluster`` is supplied.

    Returns
    -------
    pandas.DataFrame
        Columns:
            * ``cluster_id`` – int, unique identifier for each cluster.
            * ``treatment``  – int, 0 (control) or 1 (treatment), assigned at
              the cluster level.
            * ``outcome``    – float, generated outcome ``Y_ij``.
    """
    # ------------------------------------------------------------------ #
    # 1. Initialise RNG
    # ------------------------------------------------------------------ #
    set_seed(seed)

    # ------------------------------------------------------------------ #
    # 2. Validate ICC
    # ------------------------------------------------------------------ #
    if not 0.0 <= icc <= 1.0:
        raise ValueError(f"ICC must be between 0.0 and 1.0, got {icc}")

    # ------------------------------------------------------------------ #
    # 3. Determine cluster sizes
    # ------------------------------------------------------------------ #
    if isinstance(n_obs_per_cluster, int):
        # Balanced design – every cluster has the same size.
        cluster_sizes = [n_obs_per_cluster] * n_clusters
    elif isinstance(n_obs_per_cluster, list):
        if len(n_obs_per_cluster) != n_clusters:
            raise ValueError(
                f"Length of n_obs_per_cluster list ({len(n_obs_per_cluster)}) "
                f"must equal n_clusters ({n_clusters})"
            )
        cluster_sizes = n_obs_per_cluster
    else:
        # Unbalanced design – draw from a log‑normal distribution.
        # Use provided mean/std or fall back to config defaults.
        mean = cluster_mean if cluster_mean is not None else CLUSTER_MEAN_SIZE
        std = cluster_std if cluster_std is not None else CLUSTER_STD_SIZE
        mu, sigma = _lognormal_params(mean, std)

        # Draw raw sizes, then coerce to at least 1 observation per cluster.
        raw_sizes = np.random.lognormal(mean=mu, sigma=sigma, size=n_clusters)
        # Round to nearest integer and enforce a minimum of 1.
        cluster_sizes = np.maximum(np.rint(raw_sizes).astype(int), 1).tolist()

    # ------------------------------------------------------------------ #
    # 4. Warn if the design is highly unbalanced.
    # ------------------------------------------------------------------ #
    if len(cluster_sizes) > 1:
        min_size = min(cluster_sizes)
        max_size = max(cluster_sizes)
        if max_size > 5 * min_size:
            warnings.warn(
                f"Highly unbalanced cluster sizes detected: min={min_size}, max={max_size}. "
                "This may affect the stability of variance estimates."
            )

    # ------------------------------------------------------------------ #
    # 5. Compute variance components for the target ICC.
    #    We fix total variance to 1.0 (σ_b² + σ_w² = 1).
    # ------------------------------------------------------------------ #
    sigma_b_sq = icc
    sigma_w_sq = 1.0 - icc
    sigma_b = np.sqrt(sigma_b_sq)
    sigma_w = np.sqrt(sigma_w_sq)

    # ------------------------------------------------------------------ #
    # 6. Sample random intercepts (cluster effects).
    #    For icc == 0 the intercepts are exactly zero (independent data).
    # ------------------------------------------------------------------ #
    if icc == 0.0:
        cluster_intercepts = np.zeros(n_clusters)
    else:
        cluster_intercepts = np.random.normal(loc=0.0, scale=sigma_b, size=n_clusters)

    # ------------------------------------------------------------------ #
    # 7. Assign treatment at the cluster level (50 % treated).
    # ------------------------------------------------------------------ #
    treatment_assignments = np.random.choice([0, 1], size=n_clusters, p=[0.5, 0.5])

    # ------------------------------------------------------------------ #
    # 8. Assemble the dataset.
    # ------------------------------------------------------------------ #
    rows = []
    for i in range(n_clusters):
        size = cluster_sizes[i]
        u_i = cluster_intercepts[i]
        t_i = treatment_assignments[i]

        # Individual errors for all observations in this cluster.
        eps = np.random.normal(loc=0.0, scale=sigma_w, size=size)

        # Outcome: μ (0) + u_i + treatment_effect * t_i + ε_ij
        y = u_i + treatment_effect * t_i + eps

        for _ in range(size):
            rows.append(
                {
                    "cluster_id": i,
                    "treatment": int(t_i),
                    "outcome": float(y[_]),
                }
            )

    return pd.DataFrame(rows)

# The public name expected by the rest of the project.
__all__ = ["generate_data"]