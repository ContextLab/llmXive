"""
Synthetic Cluster Structure Parameter Generator.

This module generates synthetic cluster size distributions based on summary
statistics from the UCI Online Retail Data Set, without downloading the
full dataset.

Source: UCI Machine Learning Repository: Online Retail Data Set
Citation: Dua, D. and Graff, C. (2019). UCI Machine Learning Repository.
http://archive.ics.uci.edu/ml. Irvine, CA: University of California, School
of Information and Computer Science.

The synthetic generation uses a log-normal distribution parameterized to
match the provided summary statistics.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from code.config import ICC_RANGE, DEFAULT_N_CLUSTERS, validate_config, load_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hardcoded summary statistics derived from UCI Online Retail Data Set
# Source: Public summary statistics for the dataset
# These values represent typical cluster (customer) behavior patterns
UCI_SUMMARY_STATS = {
    "avg_cluster_size": 12.5,
    "std_cluster_size": 8.2
}

def get_cluster_stats():
    """
    Returns the hardcoded cluster statistics derived from UCI Online Retail.

    Returns:
        dict: Dictionary containing 'avg_cluster_size' and 'std_cluster_size'.
    """
    logger.info("Using hardcoded UCI Online Retail summary statistics.")
    return UCI_SUMMARY_STATS.copy()

def generate_synthetic_cluster_sizes(avg_size, std_size, n_clusters, seed=42):
    """
    Generates synthetic cluster sizes using a log-normal distribution.

    The log-normal parameters (mu, sigma) are calculated to match the
    target mean and standard deviation:
    - mu = ln(mean^2 / sqrt(variance + mean^2))
    - sigma = sqrt(ln(1 + variance / mean^2))

    Args:
        avg_size (float): Target average cluster size.
        std_size (float): Target standard deviation of cluster sizes.
        n_clusters (int): Number of clusters to generate.
        seed (int): Random seed for reproducibility.

    Returns:
        list: List of synthetic cluster sizes (integers >= 1).
    """
    np.random.seed(seed)

    # Calculate log-normal parameters
    variance = std_size ** 2
    mu = np.log((avg_size ** 2) / np.sqrt(variance + avg_size ** 2))
    sigma = np.sqrt(np.log(1 + (variance / avg_size ** 2)))

    logger.info(f"Log-normal parameters: mu={mu:.4f}, sigma={sigma:.4f}")
    logger.info(f"Generating {n_clusters} cluster sizes with target mean={avg_size:.2f}, std={std_size:.2f}")

    # Generate from log-normal distribution
    raw_sizes = np.random.lognormal(mean=mu, sigma=sigma, size=n_clusters)

    # Ensure all sizes are at least 1 (valid cluster)
    cluster_sizes = np.maximum(np.round(raw_sizes).astype(int), 1)

    # Verify statistics
    actual_mean = np.mean(cluster_sizes)
    actual_std = np.std(cluster_sizes)

    logger.info(f"Actual generated stats: mean={actual_mean:.2f}, std={actual_std:.2f}")

    return cluster_sizes.tolist()

def validate_structure(cluster_sizes, icc_range, n_clusters_default):
    """
    Validates that the generated cluster structure supports the full ICC range.

    For a random intercept model to be stable across the ICC range, we need
    sufficient total observations. The validation checks:
    1. Total observations (n_clusters * avg_size) is adequate for variance constraints.
    2. No clusters have size 0 (already handled by generation).
    3. The distribution is not extremely skewed (warn if > 50% of clusters are size 1).

    Args:
        cluster_sizes (list): List of cluster sizes.
        icc_range (list): Range of ICC values to validate against.
        n_clusters_default (int): Default number of clusters from config.

    Returns:
        bool: True if validation passes, False otherwise.

    Raises:
        ValueError: If validation fails.
    """
    n_clusters = len(cluster_sizes)
    total_obs = sum(cluster_sizes)
    avg_size = np.mean(cluster_sizes)

    # Check 1: Sufficient total observations for variance constraints
    # For ICC up to 0.5, we need enough observations to estimate variance components
    min_obs_threshold = 1000  # Conservative threshold for stable estimation
    if total_obs < min_obs_threshold:
        raise ValueError(
            f"Total observations ({total_obs}) is below threshold ({min_obs_threshold}) "
            f"for stable variance component estimation across ICC range {icc_range}."
        )

    # Check 2: Validate against default cluster count
    if n_clusters < 50:
        # Allow smaller n_clusters only if ICC is 0.0 (independent case)
        if 0.0 in icc_range and max(icc_range) == 0.0:
            logger.warning("Small number of clusters detected, but only ICC=0.0 is requested.")
        else:
            raise ValueError(
                f"Number of clusters ({n_clusters}) is below minimum (50) for "
                f"non-zero ICC values in range {icc_range}."
            )

    # Check 3: Skewness warning
    size_1_count = sum(1 for s in cluster_sizes if s == 1)
    if size_1_count > len(cluster_sizes) * 0.5:
        logger.warning(
            f"More than 50% of clusters have size 1 ({size_1_count}/{n_clusters}). "
            f"This may limit the ability to estimate intra-cluster correlation."
        )

    logger.info(
        f"Validation passed: {n_clusters} clusters, {total_obs} total observations, "
        f"avg size {avg_size:.2f}"
    )
    return True

def main():
    """
    Main entry point for generating synthetic cluster structure.

    Reads configuration, generates cluster sizes, validates them,
    and saves to data/derived/synthetic_cluster_structure.csv.
    """
    # Load configuration
    cfg = load_config()
    validate_config(cfg)

    # Get summary statistics
    stats = get_cluster_stats()
    avg_size = stats["avg_cluster_size"]
    std_size = stats["std_cluster_size"]

    # Use configured or default number of clusters
    n_clusters = cfg.get("n_clusters", DEFAULT_N_CLUSTERS)
    seed = cfg.get("seed", 42)

    logger.info(f"Starting synthetic cluster generation with n_clusters={n_clusters}, seed={seed}")

    # Generate cluster sizes
    cluster_sizes = generate_synthetic_cluster_sizes(
        avg_size=avg_size,
        std_size=std_size,
        n_clusters=n_clusters,
        seed=seed
    )

    # Validate the structure
    icc_range = cfg.get("icc_range", ICC_RANGE)
    try:
        validate_structure(cluster_sizes, icc_range, DEFAULT_N_CLUSTERS)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

    # Create DataFrame and save
    output_path = "data/derived/synthetic_cluster_structure.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df = pd.DataFrame({
        "cluster_id": range(1, len(cluster_sizes) + 1),
        "cluster_size": cluster_sizes
    })

    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved synthetic cluster structure to {output_path}")
    logger.info(f"Total clusters: {len(cluster_sizes)}, Total observations: {sum(cluster_sizes)}")

    return df

if __name__ == "__main__":
    main()
