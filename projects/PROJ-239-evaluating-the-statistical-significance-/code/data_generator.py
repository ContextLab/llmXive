"""
Data generator module for simulating clustered data with intra-cluster correlation.
"""

import numpy as np
import pandas as pd
from typing import List, Union, Optional
import warnings
from config import set_seed, validate_config

def generate_data(
    n_clusters: int,
    n_obs_per_cluster: Union[int, List[int]],
    icc: float,
    seed: int
) -> pd.DataFrame:
    """
    Generate simulated clustered data with intra-cluster correlation.

    Uses a random intercept model: Y_ij = mu + u_i + e_ij
    where u_i ~ N(0, sigma_u^2) and e_ij ~ N(0, sigma_e^2)

    The ICC is defined as: ICC = sigma_u^2 / (sigma_u^2 + sigma_e^2)

    Args:
        n_clusters: Number of clusters
        n_obs_per_cluster: Number of observations per cluster (can be a list for unbalanced)
        icc: Intra-cluster correlation coefficient (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        pd.DataFrame: DataFrame with columns:
                    - cluster_id: Cluster identifier
                    - treatment: Treatment assignment (0 or 1)
                    - outcome: Outcome variable
    """
    set_seed(seed)

    # Validate configuration
    cfg = {
        'n_clusters': n_clusters,
        'icc': icc
    }
    validate_config(cfg)

    # Handle unbalanced cluster sizes
    if isinstance(n_obs_per_cluster, int):
        n_obs_per_cluster = [n_obs_per_cluster] * n_clusters
    elif len(n_obs_per_cluster) != n_clusters:
        raise ValueError(f"n_obs_per_cluster must have length {n_clusters} or be an integer")

    # Check for highly unbalanced clusters
    if max(n_obs_per_cluster) > 3 * min(n_obs_per_cluster):
        warnings.warn(f"Highly unbalanced cluster sizes detected: min={min(n_obs_per_cluster)}, max={max(n_obs_per_cluster)}")

    # Set variance components based on ICC
    # Total variance = 1, so:
    # sigma_u^2 = ICC
    # sigma_e^2 = 1 - ICC
    sigma_u = np.sqrt(icc) if icc > 0 else 0
    sigma_e = np.sqrt(1 - icc)

    # Generate random intercepts (cluster effects)
    if icc == 0.0:
        # For ICC=0, random intercepts are zero (independent data)
        u = np.zeros(n_clusters)
    else:
        u = np.random.normal(0, sigma_u, n_clusters)

    # Generate data
    data_rows = []
    cluster_id = 0

    for i, n_obs in enumerate(n_obs_per_cluster):
        # Generate cluster-specific intercept
        cluster_intercept = u[i]

        # Generate observations for this cluster
        e = np.random.normal(0, sigma_e, n_obs)
        outcomes = 0 + cluster_intercept + e  # mu = 0 under H0

        # Assign treatment at cluster level (randomly)
        treatment = np.random.choice([0, 1], size=n_obs)

        for j in range(n_obs):
            data_rows.append({
                'cluster_id': cluster_id,
                'treatment': treatment[j],
                'outcome': outcomes[j]
            })

        cluster_id += 1

    df = pd.DataFrame(data_rows)
    return df
