"""
Statistical Analysis Module for llmXive Follow-up

This module implements statistical significance testing and sensitivity analysis
for comparing static vs dynamic routing models in diffusion transformers.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.benchmark import run_benchmark
from src.config import set_seed, get_results_path, ensure_directories_exist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_paired_difference_stats(static_scores: List[float], dynamic_scores: List[float]) -> Dict[str, float]:
    """
    Compute statistics on paired differences between static and dynamic model FID scores.

    Args:
        static_scores: List of FID scores from static model (same length as dynamic_scores)
        dynamic_scores: List of FID scores from dynamic model

    Returns:
        Dictionary containing mean, std, and paired difference statistics
    """
    if len(static_scores) != len(dynamic_scores):
        raise ValueError(f"Score lists must have equal length: {len(static_scores)} vs {len(dynamic_scores)}")

    if len(static_scores) == 0:
        raise ValueError("Score lists cannot be empty")

    # Compute paired differences (static - dynamic)
    differences = np.array(static_scores) - np.array(dynamic_scores)

    mean_diff = float(np.mean(differences))
    std_diff = float(np.std(differences, ddof=1))  # Sample std
    median_diff = float(np.median(differences))
    min_diff = float(np.min(differences))
    max_diff = float(np.max(differences))

    # Paired t-test
    t_stat, p_value = stats.ttest_rel(static_scores, dynamic_scores)

    return {
        "mean": mean_diff,
        "std": std_diff,
        "median": median_diff,
        "min": min_diff,
        "max": max_diff,
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "n_samples": len(differences),
        "differences": differences.tolist()
    }


def perform_bootstrap_test(
    differences: List[float],
    n_bootstrap: int = 10000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform non-parametric bootstrap test on paired differences.

    Args:
        differences: List of paired differences (static - dynamic)
        n_bootstrap: Number of bootstrap samples
        random_state: Random seed for reproducibility

    Returns:
        Dictionary containing bootstrap statistics and confidence intervals
    """
    if len(differences) == 0:
        raise ValueError("Differences list cannot be empty")

    if random_state is not None:
        np.random.seed(random_state)

    n = len(differences)
    bootstrap_means = []

    # Generate bootstrap samples
    for i in range(n_bootstrap):
        # Sample with replacement
        sample = np.random.choice(differences, size=n, replace=True)
        bootstrap_means.append(float(np.mean(sample)))

    bootstrap_means = np.array(bootstrap_means)

    # Compute confidence intervals (95%)
    ci_lower = float(np.percentile(bootstrap_means, 2.5))
    ci_upper = float(np.percentile(bootstrap_means, 97.5))

    # Compute bootstrap p-value (two-tailed test against 0)
    # P(|mean| >= |observed_mean|) under null hypothesis
    observed_mean = float(np.mean(differences))
    bootstrap_p_value = float(np.mean(np.abs(bootstrap_means) >= np.abs(observed_mean)))

    return {
        "n_bootstrap": n_bootstrap,
        "bootstrap_mean": float(np.mean(bootstrap_means)),
        "bootstrap_std": float(np.std(bootstrap_means)),
        "ci_95_lower": ci_lower,
        "ci_95_upper": ci_upper,
        "bootstrap_p_value": bootstrap_p_value,
        "observed_mean": observed_mean,
        "histogram_data": {
            "bins": np.histogram(bootstrap_means, bins=50)[0].tolist(),
            "bin_edges": np.histogram(bootstrap_means, bins=50)[1].tolist()
        }
    }


def run_benchmark_with_seed(seed: int) -> Tuple[float, float]:
    """
    Run benchmark for both static and dynamic models with a specific seed.

    Args:
        seed: Random seed for this benchmark run

    Returns:
        Tuple of (static_fid, dynamic_fid)
    """
    logger.info(f"Running benchmark with seed {seed}")
    set_seed(seed)

    # Run benchmark - this will execute both static and dynamic models
    # and return results
    results = run_benchmark(seed=seed)

    # Extract FID scores from results
    # The run_benchmark function should return a dict with both scores
    static_fid = results.get('static_fid', None)
    dynamic_fid = results.get('dynamic_fid', None)

    if static_fid is None or dynamic_fid is None:
        raise RuntimeError(f"Failed to get FID scores from benchmark run with seed {seed}")

    logger.info(f"Seed {seed}: Static FID = {static_fid:.4f}, Dynamic FID = {dynamic_fid:.4f}")

    return static_fid, dynamic_fid


def run_statistical_analysis(
    n_seeds: int = 5,
    seeds: Optional[List[int]] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.

    Args:
        n_seeds: Number of random seeds to use (default 5)
        seeds: Optional list of specific seeds to use
        output_file: Optional path to save results

    Returns:
        Dictionary containing all analysis results
    """
    if seeds is None:
        # Use 5 different seeds for reproducibility
        seeds = [42, 123, 456, 789, 101112]

    if len(seeds) != n_seeds:
        logger.warning(f"Number of seeds ({len(seeds)}) does not match n_seeds ({n_seeds}), using provided seeds")

    logger.info(f"Starting statistical analysis with {len(seeds)} seeds")
    logger.info(f"Seeds: {seeds}")

    # Ensure output directory exists
    results_path = get_results_path()
    ensure_directories_exist([results_path])

    if output_file is None:
        output_file = str(Path(results_path) / "statistical_analysis.json")

    # Collect results
    static_scores = []
    dynamic_scores = []
    seed_results = []

    for seed in seeds:
        try:
            static_fid, dynamic_fid = run_benchmark_with_seed(seed)
            static_scores.append(static_fid)
            dynamic_scores.append(dynamic_fid)

            seed_results.append({
                "seed": seed,
                "static_fid": static_fid,
                "dynamic_fid": dynamic_fid,
                "difference": static_fid - dynamic_fid
            })

        except Exception as e:
            logger.error(f"Failed to run benchmark with seed {seed}: {e}")
            raise

    # Compute paired difference statistics
    paired_stats = compute_paired_difference_stats(static_scores, dynamic_scores)
    logger.info(f"Paired difference stats: mean={paired_stats['mean']:.4f}, std={paired_stats['std']:.4f}")

    # Perform bootstrap test
    bootstrap_results = perform_bootstrap_test(
        paired_stats["differences"],
        n_bootstrap=10000,
        random_state=42
    )
    logger.info(f"Bootstrap p-value: {bootstrap_results['bootstrap_p_value']:.4f}")

    # Compile final results
    results = {
        "analysis_config": {
            "n_seeds": len(seeds),
            "seeds": seeds,
            "static_scores": static_scores,
            "dynamic_scores": dynamic_scores
        },
        "paired_difference": {
            "mean": paired_stats["mean"],
            "std": paired_stats["std"],
            "median": paired_stats["median"],
            "min": paired_stats["min"],
            "max": paired_stats["max"],
            "t_statistic": paired_stats["t_statistic"],
            "p_value": paired_stats["p_value"],
            "n_samples": paired_stats["n_samples"]
        },
        "bootstrap_results": {
            "n_bootstrap": bootstrap_results["n_bootstrap"],
            "bootstrap_mean": bootstrap_results["bootstrap_mean"],
            "bootstrap_std": bootstrap_results["bootstrap_std"],
            "ci_95_lower": bootstrap_results["ci_95_lower"],
            "ci_95_upper": bootstrap_results["ci_95_upper"],
            "bootstrap_p_value": bootstrap_results["bootstrap_p_value"],
            "observed_mean": bootstrap_results["observed_mean"]
        },
        "individual_results": seed_results,
        "statistical_significance": {
            "is_significant_alpha_05": paired_stats["p_value"] < 0.05,
            "is_significant_alpha_01": paired_stats["p_value"] < 0.01,
            "bootstrap_significant": bootstrap_results["bootstrap_p_value"] < 0.05,
            "ci_excludes_zero": not (bootstrap_results["ci_95_lower"] <= 0 <= bootstrap_results["ci_95_upper"])
        },
        "limitations": {
            "note": "Small sample size (N=5) limits statistical power. Results should be interpreted with caution.",
            "recommendation": "Consider increasing sample size for more robust conclusions."
        }
    }

    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Statistical analysis results saved to {output_file}")

    return results


def main():
    """Main entry point for statistical analysis."""
    logger.info("Starting statistical analysis (T025)")

    try:
        results = run_statistical_analysis(
            n_seeds=5,
            seeds=[42, 123, 456, 789, 101112]
        )

        # Print summary
        print("\n" + "="*60)
        print("STATISTICAL ANALYSIS SUMMARY")
        print("="*60)
        print(f"Number of seeds: {results['analysis_config']['n_seeds']}")
        print(f"Mean paired difference (static - dynamic): {results['paired_difference']['mean']:.4f}")
        print(f"Standard deviation: {results['paired_difference']['std']:.4f}")
        print(f"Paired t-test p-value: {results['paired_difference']['p_value']:.4f}")
        print(f"Bootstrap p-value: {results['bootstrap_results']['bootstrap_p_value']:.4f}")
        print(f"95% CI: [{results['bootstrap_results']['ci_95_lower']:.4f}, {results['bootstrap_results']['ci_95_upper']:.4f}]")
        print(f"Statistically significant (α=0.05): {results['statistical_significance']['is_significant_alpha_05']}")
        print("="*60)

        return results

    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
