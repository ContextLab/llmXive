"""
MaxT Procedure for FWER Control across Window Pairs.

This module implements the MaxT step-down procedure to control the Family-Wise Error Rate (FWER)
for dependent test statistics (JS divergences between temporal windows).
Per the project plan, MaxT is preferred over Benjamini-Hochberg due to the
dependence structure of the temporal windows.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
from scipy import stats

from src.utils.logging import get_logger

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_N_BOOTSTRAP = 10000
RNG_SEED = 42

logger = get_logger(__name__)


def compute_max_t_statistics(
    observed_js: np.ndarray,
    permuted_js_matrix: np.ndarray,
    n_permutations: int = 10000,
    random_seed: int = RNG_SEED
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the MaxT critical values and adjusted p-values.

    The MaxT procedure works by:
    1. For each permutation iteration, computing the maximum test statistic across all hypotheses.
    2. Using the distribution of these maximums to determine the critical value for the desired alpha.
    3. Adjusting p-values based on the proportion of max-statistics exceeding the observed statistic.

    Args:
        observed_js: Array of observed Jensen-Shannon divergences for each window pair.
        permuted_js_matrix: Matrix of shape (n_permutations, n_hypotheses) containing
                            JS divergences from the null distribution for each hypothesis.
        n_permutations: Number of permutations to consider for the MaxT distribution.
        random_seed: Seed for reproducibility.

    Returns:
        Tuple containing:
            - adjusted_pvalues: Array of adjusted p-values for each hypothesis.
            - max_t_distribution: The distribution of maximum statistics from permutations.
    """
    rng = np.random.default_rng(random_seed)
    n_hypotheses = len(observed_js)

    if permuted_js_matrix.shape[0] < n_permutations:
        logger.warning(
            f"Requested {n_permutations} permutations but only {permuted_js_matrix.shape[0]} available. "
            "Using available data."
        )
        n_permutations = permuted_js_matrix.shape[0]

    # Shuffle rows to simulate null distribution variability if needed, 
    # but typically permuted_js_matrix is already generated via stratified sampling.
    # We take the max across hypotheses for each permutation row.
    max_stats = np.max(permuted_js_matrix[:n_permutations], axis=1)

    # Calculate adjusted p-values for each observed statistic
    # p_adj(h) = P(max(T) >= observed(h)) under the null
    adjusted_pvalues = np.zeros(n_hypotheses)
    for i in range(n_hypotheses):
        obs_val = observed_js[i]
        # Count how many max statistics are greater than or equal to the observed value
        count = np.sum(max_stats >= obs_val)
        adjusted_pvalues[i] = count / n_permutations

    return adjusted_pvalues, max_stats


def apply_maxt_correction(
    observed_js: np.ndarray,
    permuted_js_matrix: np.ndarray,
    alpha: float = DEFAULT_ALPHA,
    n_permutations: int = DEFAULT_N_BOOTSTRAP,
    random_seed: int = RNG_SEED
) -> Dict[str, Any]:
    """
    Apply the MaxT procedure to control FWER.

    Args:
        observed_js: Observed JS divergence values for each window pair.
        permuted_js_matrix: Matrix of shape (n_permutations, n_hypotheses) from the permutation test.
        alpha: Significance level (default 0.05).
        n_permutations: Number of permutations to use for the max distribution.
        random_seed: Random seed for reproducibility.

    Returns:
        Dictionary containing:
            - 'adjusted_pvalues': Array of adjusted p-values.
            - 'significant': Boolean array indicating which hypotheses are significant after correction.
            - 'critical_value': The MaxT critical value at the specified alpha.
            - 'max_t_distribution': The distribution of maximum statistics.
            - 'n_permutations': Number of permutations actually used.
    """
    logger.info(f"Applying MaxT correction with alpha={alpha}, n_permutations={n_permutations}")

    adjusted_pvalues, max_t_dist = compute_max_t_statistics(
        observed_js, permuted_js_matrix, n_permutations, random_seed
    )

    # Determine significance
    significant = adjusted_pvalues <= alpha

    # Calculate critical value (the (1-alpha) quantile of the max distribution)
    if len(max_t_dist) > 0:
        critical_value = float(np.percentile(max_t_dist, 100 * (1 - alpha)))
    else:
        critical_value = float(np.inf)
        logger.warning("MaxT distribution is empty; cannot compute critical value.")

    return {
        "adjusted_pvalues": adjusted_pvalues.tolist(),
        "significant": significant.tolist(),
        "critical_value": critical_value,
        "max_t_distribution": max_t_dist.tolist(),
        "n_permutations": int(n_permutations),
        "alpha": alpha
    }


def save_correction_results(
    results: Dict[str, Any],
    output_path: Union[str, Path],
    window_pairs: List[Tuple[str, str]]
) -> None:
    """
    Save MaxT correction results to a JSON file.

    Args:
        results: Dictionary containing correction results.
        output_path: Path to the output JSON file.
        window_pairs: List of tuples representing the window pairs corresponding to the hypotheses.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Format results for human readability
    formatted_results = {
        "maxt_correction": {
            "alpha": results["alpha"],
            "critical_value": results["critical_value"],
            "n_permutations_used": results["n_permutations"]
        },
        "hypotheses": []
    }

    for i, (pair) in enumerate(window_pairs):
        formatted_results["hypotheses"].append({
            "pair": f"{pair[0]} vs {pair[1]}",
            "adjusted_pvalue": results["adjusted_pvalues"][i],
            "is_significant": results["significant"][i]
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, indent=2)

    logger.info(f"MaxT correction results saved to {output_path}")


def load_permutation_data(
    permutation_file_path: Union[str, Path]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load observed JS divergences and permuted matrix from the permutation test output.

    Args:
        permutation_file_path: Path to the JSON file containing permutation test results.

    Returns:
        Tuple of (observed_js, permuted_matrix).
    """
    with open(permutation_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    observed = np.array(data["observed_js_divergences"])
    permuted = np.array(data["null_distribution"])

    return observed, permuted


def main() -> None:
    """
    Main entry point to run MaxT correction.
    Expects permutation test results in results/stats/permutation_results.json.
    Saves output to results/stats/maxt_correction_results.json.
    """
    logger.info("Starting MaxT Correction Process")

    # Define paths
    base_path = Path(__file__).parent.parent.parent.parent
    permutation_input = base_path / "results" / "stats" / "permutation_results.json"
    output_path = base_path / "results" / "stats" / "maxt_correction_results.json"
    window_pairs_file = base_path / "results" / "stats" / "window_pairs.json"

    if not permutation_input.exists():
        logger.error(f"Permutation results file not found: {permutation_input}")
        logger.error("Please run the permutation test (T029) first.")
        return

    if not window_pairs_file.exists():
        logger.error(f"Window pairs file not found: {window_pairs_file}")
        logger.error("Cannot map results to specific window pairs.")
        return

    # Load data
    try:
        observed_js, permuted_matrix = load_permutation_data(permutation_input)
        with open(window_pairs_file, 'r', encoding='utf-8') as f:
            window_pairs = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # Apply correction
    results = apply_maxt_correction(
        observed_js=observed_js,
        permuted_js_matrix=permuted_matrix,
        alpha=0.05,
        n_permutations=10000,
        random_seed=42
    )

    # Save results
    save_correction_results(results, output_path, window_pairs)

    # Log summary
    n_sig = sum(results["significant"])
    total = len(results["significant"])
    logger.info(f"MaxT Correction Complete: {n_sig}/{total} hypotheses significant at alpha=0.05")
    logger.info(f"Critical Value (MaxT): {results['critical_value']:.4f}")


if __name__ == "__main__":
    main()