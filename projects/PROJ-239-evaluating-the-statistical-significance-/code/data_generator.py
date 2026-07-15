"""
Data generator module for simulating A/B test results with intra-cluster correlation.

This module implements a random intercept model to generate synthetic data that
exhibits intra-cluster correlation (ICC). The model is defined as:

    Y_ij = mu + u_i + e_ij

where:
    - Y_ij is the outcome for observation j in cluster i.
    - mu is the global mean (set to 0 for simplicity).
    - u_i is the random intercept for cluster i, u_i ~ N(0, sigma_b^2).
    - e_ij is the individual error term, e_ij ~ N(0, sigma_w^2).

The Intraclass Correlation Coefficient (ICC) is defined as:
    ICC = sigma_b^2 / (sigma_b^2 + sigma_w^2)

Simulation Parameters (Principle VII - Transparency):
-----------------------------------------------------
ICC Range: The generator supports ICC values from 0.0 to 1.0.
           In the context of the full simulation pipeline (T012, T019, T031),
           ICC values are typically simulated from 0.0 to 0.5 in increments of 0.1.
           This range is chosen because ICC > 0.5 is rare in typical A/B testing
           scenarios (e.g., web analytics, user sessions).
           - ICC = 0.0: Independent observations (no cluster effect).
           - ICC = 0.1 to 0.5: Moderate correlation, common in clustered data.

Iteration Count: The generator itself does not control iteration count; this is
                 managed by the simulation runner (simulation_runner.py).
                 However, the generator is designed to be called repeatedly in
                 loops (typically 1,000 iterations per ICC level) to build
                 empirical distributions of test statistics.

Random Seed: Reproducibility is ensured by setting a global random seed at the
             start of each simulation run. The default seed is 42 (as defined in
             config.py). The generator uses this seed via `set_seed()` before
             generating random numbers.

Edge Cases:
-----------
- ICC = 0.0: The random intercept u_i is set to exactly 0.0, resulting in
             independent observations. This is a critical edge case for
             validating that the naive t-test behaves correctly under independence.
- Unbalanced Clusters: The generator accepts a list of cluster sizes. If the
                       sizes are highly unbalanced (max > 5 * min), a warning
                       is issued to alert the user of potential instability in
                       variance estimates.

Usage:
------
This module is primarily used by `simulation_runner.py` to generate data for
each iteration of the simulation. It is not intended for direct use in production
analysis but serves as the data generation engine for the research pipeline.

Note on Principle VI:
---------------------
This generator creates data with cluster structure. However, the naive t-test
(used as a baseline) intentionally ignores this structure, violating Principle VI
(Cluster-Aware Inference). This violation is deliberate to measure the inflation
of Type I error rates when cluster correlation is ignored.
"""
import warnings
import numpy as np
import pandas as pd
from typing import List, Optional, Union
from code.config import set_seed

def generate_data(
    n_clusters: int,
    n_obs_per_cluster: Union[int, List[int]],
    icc: float,
    seed: int,
    treatment_effect: float = 0.0
) -> pd.DataFrame:
    """
    Generate synthetic A/B test data with cluster-level correlation.

    This function implements the random intercept model: Y_ij = mu + u_i + e_ij.
    It supports both balanced (single int) and unbalanced (list of ints) cluster sizes.

    Parameters
    ----------
    n_clusters : int
        Number of clusters to generate. Must be >= 50 unless icc == 0.0 (see validation in config).
    n_obs_per_cluster : int or list of int
        Number of observations per cluster.
        - If int: All clusters have this size.
        - If list: Must have length `n_clusters`. Each element is the size of that cluster.
    icc : float
        Intraclass Correlation Coefficient (0.0 to 1.0).
        - If 0.0: No random intercept is added (independent data).
        - If > 0.0: Random intercepts are drawn from N(0, sigma_b^2).
    seed : int
        Random seed for reproducibility. The default seed used in the project is 42.
    treatment_effect : float, default 0.0
        The effect size of the treatment (difference in means between treatment and control).
        Set to 0.0 for Null Hypothesis (H0) testing (Type I error simulation).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        - 'cluster_id': int, unique identifier for each cluster.
        - 'treatment': int, 0 (control) or 1 (treatment). Assigned at cluster level.
        - 'outcome': float, the generated outcome value.

    Raises
    ------
    ValueError
        If icc is outside [0, 1].
        If n_obs_per_cluster is a list and its length does not match n_clusters.
    Warning
        If cluster sizes are highly unbalanced (max > 5 * min).

    Simulation Transparency (Principle VII):
    ----------------------------------------
    - ICC Range: Supports 0.0 to 1.0. Typical simulations use 0.0 to 0.5.
    - Iterations: Controlled by caller (e.g., simulation_runner.py runs 1,000 iterations).
    - Seed: Default 42. Ensures reproducible random number generation.
    """
    set_seed(seed)

    if not 0.0 <= icc <= 1.0:
        raise ValueError(f"ICC must be between 0.0 and 1.0, got {icc}")

    # Handle n_obs_per_cluster
    if isinstance(n_obs_per_cluster, int):
        cluster_sizes = [n_obs_per_cluster] * n_clusters
    else:
        if len(n_obs_per_cluster) != n_clusters:
            raise ValueError(f"n_obs_per_cluster list length ({len(n_obs_per_cluster)}) "
                             f"must match n_clusters ({n_clusters})")
        cluster_sizes = n_obs_per_cluster

    # Check for highly unbalanced clusters and warn
    if len(cluster_sizes) > 1:
        min_size = min(cluster_sizes)
        max_size = max(cluster_sizes)
        if max_size > 5 * min_size:
            warnings.warn(
                f"Highly unbalanced cluster sizes detected: min={min_size}, max={max_size}. "
                "This may affect the stability of variance estimates."
            )

    # Calculate variance components
    # Total variance = 1.0 for simplicity
    # ICC = sigma_b^2 / (sigma_b^2 + sigma_w^2)
    # Let sigma_b^2 + sigma_w^2 = 1
    sigma_b_sq = icc
    sigma_w_sq = 1.0 - icc

    sigma_b = np.sqrt(sigma_b_sq)
    sigma_w = np.sqrt(sigma_w_sq)

    # Generate random intercepts (cluster effects)
    # If icc == 0.0, u_i is exactly 0 (independent data case)
    if icc == 0.0:
        u = np.zeros(n_clusters)
    else:
        u = np.random.normal(0, sigma_b, n_clusters)

    # Generate treatment assignment (cluster level)
    # Randomly assign 50% of clusters to treatment
    treatment_assignments = np.random.choice([0, 1], size=n_clusters, p=[0.5, 0.5])

    data_rows = []
    cluster_id = 0

    for i in range(n_clusters):
        size = cluster_sizes[i]
        cluster_u = u[i]
        cluster_treatment = treatment_assignments[i]

        # Generate individual errors
        e = np.random.normal(0, sigma_w, size)

        # Generate outcome
        # Y_ij = mu + u_i + (treatment_effect * cluster_treatment) + e_ij
        # Assume mu = 0
        y = cluster_u + (treatment_effect * cluster_treatment) + e

        for j in range(size):
            data_rows.append({
                'cluster_id': cluster_id,
                'treatment': cluster_treatment,
                'outcome': y[j]
            })

        cluster_id += 1

    return pd.DataFrame(data_rows)