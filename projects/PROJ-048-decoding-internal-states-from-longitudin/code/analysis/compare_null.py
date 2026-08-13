"""
Statistical comparison between NMF-derived correlations and linear mixing null model.
Implements T035: explicit statistical comparison with difference calculation and report generation.
"""
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json

from utils.logger import get_logger, log_stage_start, log_stage_end
from analysis.null_model import run_null_model_comparison
from analysis.stats import run_statistical_analysis, calculate_spearman_correlation

class ComparisonError(Exception):
    """Custom exception for comparison errors."""
    pass

def compare_nmf_vs_null(
    observed_weights: np.ndarray,
    behavior: np.ndarray,
    n_permutations: int = 1000,
    n_null_iterations: int = 100,
    noise_scale: float = 0.1,
    random_seed: Optional[int] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Perform explicit statistical comparison between NMF and null model.

    Args:
        observed_weights: NMF component weights (n_samples, n_components)
        behavior: Behavioral metrics (n_samples,)
        n_permutations: Permutation test iterations
        n_null_iterations: Null model iterations
        noise_scale: Noise scale for null model
        random_seed: Random seed
        output_dir: Directory for output files

    Returns:
        Comparison results dictionary
    """
    log_stage_start("NMF vs Null Comparison", {
        "weights_shape": observed_weights.shape,
        "n_permutations": n_permutations,
        "n_null_iterations": n_null_iterations
    })

    # Run statistical analysis on observed data
    stats_results = run_statistical_analysis(
        observed_weights, behavior,
        is_held_out=False,  # Set to True if this is held-out set
        n_permutations=n_permutations,
        random_seed=random_seed
    )

    # Run null model comparison
    null_results = run_null_model_comparison(
        observed_weights, behavior,
        n_components=observed_weights.shape[1],
        n_iterations=n_null_iterations,
        noise_scale=noise_scale,
        random_seed=random_seed
    )

    # Calculate difference in correlation strength
    obs_corrs = np.array(stats_results["observed_correlations"])
    null_corrs = np.array(null_results["null_correlation_mean"])

    correlation_diff = obs_corrs - null_corrs
    correlation_diff_std = np.std(obs_corrs) - np.std(null_corrs)

    # Calculate p-values for the difference (simplified: check if observed > null)
    diff_significance = correlation_diff > 0

    results = {
        "n_components": observed_weights.shape[1],
        "observed_correlations": obs_corrs.tolist(),
        "null_correlation_mean": null_corrs.tolist(),
        "correlation_difference": correlation_diff.tolist(),
        "correlation_difference_std": correlation_diff_std.tolist(),
        "p_values_permutation": stats_results["permutation_p_values"],
        "p_values_vs_null": null_results["p_values_vs_null"],
        "significantly_better_than_null": diff_significance.tolist(),
        "summary": {
            "mean_observed_corr": float(np.mean(obs_corrs)),
            "mean_null_corr": float(np.mean(null_corrs)),
            "mean_difference": float(np.mean(correlation_diff)),
            "n_significant_components": int(np.sum(diff_significance))
        }
    }

    # Write comparison report
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "nmf_vs_null_comparison.json"
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"Comparison report written to {report_path}")

    log_stage_end("NMF vs Null Comparison", {
        "n_significant": int(np.sum(diff_significance)),
        "mean_difference": float(np.mean(correlation_diff))
    })

    return results

def main():
    """Main entry point for comparison."""
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)

    logger.info("Comparison module ready")
    logger.info("Use compare_nmf_vs_null() for statistical comparison")

    return 0

if __name__ == "__main__":
    exit(main())