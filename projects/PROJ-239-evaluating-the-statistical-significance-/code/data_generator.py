"""
Data generator module for simulating A/B test results with intra-cluster correlation.

Implements a random intercept model: Y_ij = mu + u_i + e_ij
where u_i ~ N(0, sigma_b^2) and e_ij ~ N(0, sigma_w^2).
ICC = sigma_b^2 / (sigma_b^2 + sigma_w^2)

NOTE: This baseline method intentionally violates Principle VI (Cluster-Aware Inference)
to measure Type I error inflation. It must be clearly documented as a "violation baseline"
for comparison only.
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

    Parameters
    ----------
    n_clusters : int
        Number of clusters to generate.
    n_obs_per_cluster : int or list of int
        Number of observations per cluster. If int, all clusters have this size.
        If list, must have length `n_clusters`.
    icc : float
        Intraclass Correlation Coefficient (0.0 to 1.0).
        If 0.0, no random intercept is added (independent data).
    seed : int
        Random seed for reproducibility.
    treatment_effect : float, default 0.0
        The effect size of the treatment (difference in means).
        Set to 0.0 for Null Hypothesis (H0) testing.

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: 'cluster_id', 'treatment', 'outcome'

    Raises
    ------
    ValueError
        If icc is outside [0, 1] or if n_obs_per_cluster list length mismatch.
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