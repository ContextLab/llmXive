"""
permutation_report.py

Generates a visual report of the permutation test null distribution for the
relationship between brain network reconfigurability (transition count) and
subjective time perception (DSST score). The script:

1. Loads the aggregated metric/behavior data using the existing analysis
   utilities.
2. Computes the observed Spearman correlation.
3. Performs a seeded permutation test (default 1000 permutations),
   shuffling the behavioral scores while keeping the metric values fixed.
4. Writes the full null distribution to
   ``data/results/permutation_results.tsv`` with columns
   ``shuffle_index`` and ``spearman_rho``.
5. Creates a histogram of the null distribution, highlights the observed
   statistic, and saves the figure to
   ``data/results/permutation_report.png``.
6. Logs progress to the standard logger (which writes to
   ``data/analysis_log.txt`` via ``utils.setup_logger``).

The script is deliberately self‑contained and can be invoked from the
quick‑start run‑book with ``python code/permutation_report.py``.
"""

import logging
import os
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Local imports – these are part of the project's public API
from analysis import load_metrics_and_behavioral_data, compute_spearman
from utils import setup_logger, get_seeded_rng

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DEFAULT_PERMUTATIONS = 1000
OUTPUT_TSV = Path("data/results/permutation_results.tsv")
OUTPUT_PNG = Path("data/results/permutation_report.png")
LOG_FILE = Path("data/analysis_log.txt")

# Ensure output directories exist
OUTPUT_TSV.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def run_permutation_test(
    metric_vals: np.ndarray,
    behavior_vals: np.ndarray,
    n_perm: int = DEFAULT_PERMUTATIONS,
    rng_seed: int = 42,
) -> Tuple[float, List[float]]:
    """
    Perform a permutation test.

    Parameters
    ----------
    metric_vals : np.ndarray
        Array of reconfigurability metric values (e.g., transition counts).
    behavior_vals : np.ndarray
        Array of behavioral scores (e.g., DSST scores).
    n_perm : int, optional
        Number of permutations, by default 1000.
    rng_seed : int, optional
        Seed for reproducibility, by default 42.

    Returns
    -------
    observed_rho : float
        Spearman correlation on the original (unshuffled) data.
    null_rhos : List[float]
        List of Spearman correlations obtained from each permutation.
    """
    logger = logging.getLogger(__name__)

    # Compute the observed statistic once
    observed_rho, _ = compute_spearman(metric_vals, behavior_vals)
    logger.debug(f"Observed Spearman rho: {observed_rho:.5f}")

    rng = get_seeded_rng(rng_seed)
    null_rhos: List[float] = []

    for i in range(n_perm):
        shuffled_beh = rng.permutation(behavior_vals)
        rho, _ = compute_spearman(metric_vals, shuffled_beh)
        null_rhos.append(rho)

        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation {i + 1}/{n_perm} completed")

    return observed_rho, null_rhos

def save_null_distribution(null_rhos: List[float], path: Path) -> None:
    """Write the null distribution to a TSV file."""
    df = pd.DataFrame(
        {"shuffle_index": np.arange(len(null_rhos)), "spearman_rho": null_rhos}
    )
    df.to_csv(path, sep="\t", index=False)

def plot_permutation_report(
    null_rhos: List[float],
    observed_rho: float,
    out_path: Path,
) -> None:
    """Create and save the histogram plot."""
    plt.figure(figsize=(8, 5))
    plt.hist(null_rhos, bins=30, color="#4c72b0", alpha=0.7, edgecolor="black")
    plt.axvline(
        observed_rho,
        color="red",
        linestyle="dashed",
        linewidth=2,
        label=f"Observed ρ = {observed_rho:.3f}",
    )
    plt.title("Permutation Test Null Distribution")
    plt.xlabel("Spearman ρ")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the permutation‑test report generation.
    """
    # Initialise logger (writes to data/analysis_log.txt)
    logger = setup_logger(log_file=LOG_FILE)

    logger.info("Starting permutation‑test report generation")

    # Load the aggregated metric and behavioral data.
    # The helper returns two 1‑D NumPy arrays: metrics and DSST scores.
    metric_vals, behavior_vals = load_metrics_and_behavioral_data()
    metric_vals = np.asarray(metric_vals)
    behavior_vals = np.asarray(behavior_vals)

    # Run the permutation test.
    observed_rho, null_rhos = run_permutation_test(
        metric_vals, behavior_vals, n_perm=DEFAULT_PERMUTATIONS, rng_seed=42
    )

    # Persist the null distribution.
    save_null_distribution(null_rhos, OUTPUT_TSV)
    logger.info(f"Null distribution saved to {OUTPUT_TSV}")

    # Generate the histogram figure.
    plot_permutation_report(null_rhos, observed_rho, OUTPUT_PNG)
    logger.info(f"Permutation report figure saved to {OUTPUT_PNG}")

    logger.info("Permutation‑test report generation completed successfully")

if __name__ == "__main__":
    main()
