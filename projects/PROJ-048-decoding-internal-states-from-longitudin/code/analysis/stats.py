"""
Statistical analysis module for User Story 3.
Implements Spearman correlation, permutation tests, and Benjamini-Hochberg FDR correction.
"""
import numpy as np
import logging
from scipy.stats import spearmanr
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json
import time

from utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage
from config import get_config_value

class StatsError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def calculate_spearman_correlation(
    weights: np.ndarray,
    behavior: np.ndarray
) -> Tuple[float, float]:
    """
    Calculate Spearman correlation between component weights and behavioral metrics.

    Args:
        weights: NMF component weights (n_samples, n_components)
        behavior: Behavioral metrics (n_samples,)

    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    if weights.shape[0] != behavior.shape[0]:
        raise StatsError(
            f"Shape mismatch: weights has {weights.shape[0]} samples, "
            f"behavior has {behavior.shape[0]} samples"
        )

    correlations = []
    p_values = []

    for i in range(weights.shape[1]):
        corr, p_val = spearmanr(weights[:, i], behavior)
        correlations.append(corr)
        p_values.append(p_val)

    return np.array(correlations), np.array(p_values)

def permutation_test(
    weights: np.ndarray,
    behavior: np.ndarray,
    n_iterations: int = 1000,
    random_seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Perform permutation test to generate null distribution and p-values.

    Args:
        weights: NMF component weights (n_samples, n_components)
        behavior: Behavioral metrics (n_samples,)
        n_iterations: Number of permutation iterations for statistical reliability
        random_seed: Random seed for reproducibility

    Returns:
        Tuple of (observed_correlations, observed_p_values, null_distributions, p_values_permutation)
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    n_samples = weights.shape[0]
    n_components = weights.shape[1]

    # Calculate observed correlations
    observed_correlations, observed_p_values = calculate_spearman_correlation(weights, behavior)

    # Initialize null distributions
    null_distributions = np.zeros((n_iterations, n_components))

    log_stage_start("Permutation Test", f"{n_iterations} iterations")

    for i in range(n_iterations):
        if (i + 1) % 100 == 0:
            logging.info(f"Permutation iteration {i + 1}/{n_iterations}")

        # Shuffle behavior data
        shuffled_behavior = np.random.permutation(behavior)

        # Calculate correlation with shuffled data
        shuffled_corrs, _ = calculate_spearman_correlation(weights, shuffled_behavior)
        null_distributions[i, :] = shuffled_corrs

    # Calculate p-values from permutation distribution
    # Two-tailed test: p = proportion of null values >= |observed|
    p_values_permutation = np.zeros(n_components)
    for j in range(n_components):
        obs_abs = abs(observed_correlations[j])
        null_abs = np.abs(null_distributions[:, j])
        p_values_permutation[j] = np.sum(null_abs >= obs_abs) / n_iterations

    log_stage_end("Permutation Test", {
        "iterations": n_iterations,
        "p_values": p_values_permutation.tolist()
    })

    return observed_correlations, observed_p_values, null_distributions, p_values_permutation

def benjamini_hochberg_fdr(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.

    Args:
        p_values: Array of p-values
        alpha: Significance threshold

    Returns:
        Tuple of (adjusted_p_values, significant_flags)
    """
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([])

    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Calculate adjusted p-values
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        # BH formula: p_adj = p * n / rank
        rank = i + 1
        adjusted_p_values[sorted_indices[i]] = sorted_p_values[i] * n / rank

    # Ensure adjusted p-values don't exceed 1
    adjusted_p_values = np.minimum(adjusted_p_values, 1.0)

    # Make monotonic (cumulative minimum from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p_values[sorted_indices[i]] = min(
            adjusted_p_values[sorted_indices[i]],
            adjusted_p_values[sorted_indices[i + 1]]
        )

    # Determine significance
    significant_flags = adjusted_p_values < alpha

    return adjusted_p_values, significant_flags

def run_statistical_analysis(
    weights: np.ndarray,
    behavior: np.ndarray,
    is_held_out: bool = False,
    n_permutations: int = 1000,
    random_seed: Optional[int] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run complete statistical analysis pipeline.

    Args:
        weights: NMF component weights (n_samples, n_components)
        behavior: Behavioral metrics (n_samples,)
        is_held_out: Whether this is the held-out test set (enables FDR correction)
        n_permutations: Number of permutation iterations
        random_seed: Random seed for reproducibility
        output_dir: Directory to write results

    Returns:
        Dictionary containing all analysis results
    """
    log_stage_start("Statistical Analysis", {
        "weights_shape": weights.shape,
        "behavior_shape": behavior.shape,
        "is_held_out": is_held_out
    })

    # Run permutation test
    observed_corrs, observed_p_vals, null_dist, p_vals_perm = permutation_test(
        weights, behavior, n_iterations=n_permutations, random_seed=random_seed
    )

    # Apply FDR correction ONLY if this is the held-out set
    if is_held_out:
        adjusted_p_vals, significant_flags = benjamini_hochberg_fdr(p_vals_perm)
        logging.info("Applied Benjamini-Hochberg FDR correction to held-out set")
    else:
        adjusted_p_vals = p_vals_perm
        significant_flags = p_vals_perm < 0.05
        logging.info("Skipped FDR correction (not held-out set)")

    results = {
        "weights_shape": weights.shape.tolist(),
        "behavior_shape": behavior.shape.tolist(),
        "is_held_out": is_held_out,
        "n_permutations": n_permutations,
        "random_seed": random_seed,
        "observed_correlations": observed_corrs.tolist(),
        "observed_p_values": observed_p_vals.tolist(),
        "permutation_p_values": p_vals_perm.tolist(),
        "adjusted_p_values": adjusted_p_vals.tolist(),
        "significant_flags": significant_flags.tolist(),
        "null_distribution_stats": {
            "mean": np.mean(null_dist, axis=0).tolist(),
            "std": np.std(null_dist, axis=0).tolist(),
            "min": np.min(null_dist, axis=0).tolist(),
            "max": np.max(null_dist, axis=0).tolist()
        }
    }

    # Write results to file if output_dir provided
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "statistical_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"Results written to {output_file}")

    log_stage_end("Statistical Analysis", {
        "significant_components": int(np.sum(significant_flags)),
        "fdr_applied": is_held_out
    })

    return results

def main():
    """Main entry point for statistical analysis."""
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)

    # Load configuration
    random_seed = get_config_value("RANDOM_SEED", 42)
    n_permutations = int(get_config_value("N_PERMUTATIONS", 1000))

    logger.info(f"Starting statistical analysis with seed={random_seed}, permutations={n_permutations}")

    # This would normally load real data from previous stages
    # For now, we log the configuration
    logger.info("Statistical analysis module ready")
    logger.info("Use run_statistical_analysis() with real weights and behavior data")

    return 0

if __name__ == "__main__":
    exit(main())
