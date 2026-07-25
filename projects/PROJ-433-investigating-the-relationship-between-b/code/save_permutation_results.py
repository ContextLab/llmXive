"""
Task T034: Save permutation test raw results and null distribution data.

This script runs the permutation test logic from code/analysis.py and saves:
1. The raw results (observed statistic, permutation p-value, etc.)
2. The full null distribution data to a TSV file.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Import from existing API surface
from analysis import load_metrics_and_behavioral_data, run_permutation_test, calculate_permutation_p_value
from utils import setup_logger, get_seeded_rng

def save_permutation_results(
    output_path: str = "data/results/permutation_results.tsv",
    n_permutations: int = 5000,
    seed: int = 42
) -> None:
    """
    Executes the permutation test and saves the raw results and null distribution.

    Args:
        output_path: Path to the output TSV file.
        n_permutations: Number of permutations to run.
        seed: Random seed for reproducibility.
    """
    logger = setup_logger("analysis")
    logger.info(f"Starting permutation test with {n_permutations} permutations.")

    # Load data
    # This function is expected to return (metrics_array, dsst_array, subject_ids)
    # based on the context of previous tasks (T025, T032).
    try:
        metrics, dsst_scores, subject_ids = load_metrics_and_behavioral_data()
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        # Fail loudly as per constraints
        raise RuntimeError("Data loading failed. Cannot proceed with permutation test.") from e

    if len(metrics) == 0 or len(dsst_scores) == 0:
        logger.warning("No valid data found for permutation test.")
        # Create an empty result file to indicate completion with no data
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["metric_pair", "observed_stat", "null_mean", "null_std", "p_value_perm", "n_permutations"]).to_csv(output_path, sep="\t", index=False)
        return

    # Run permutation test
    # run_permutation_test returns (observed_stat, null_distribution, p_value)
    # We assume the function signature matches the logic in T032/T033
    observed_stat, null_distribution, p_val_perm = run_permutation_test(
        metrics, dsst_scores, n_permutations=n_permutations, seed=seed
    )

    logger.info(f"Permutation test complete. Observed stat: {observed_stat:.4f}, P-value: {p_val_perm:.4f}")

    # Prepare results DataFrame
    # Structure: One row for the summary, or one row per permutation?
    # The task asks for "raw results and null distribution data".
    # Best practice for TSV:
    # Option A: Summary row + null distribution rows.
    # Option B: Two files.
    # Given the single path constraint, we will save the Null Distribution as the main body
    # and include the observed stat in the metadata or as a separate header row if possible,
    # but standard TSV is usually uniform.
    # Let's create a file where the first row is the observed stats summary,
    # and subsequent rows are the null distribution samples.
    # However, a cleaner approach for "raw results" often implies the distribution.
    # Let's save a file with columns: [sample_id, null_value, is_observed]
    # And include the observed stat in the metadata or as a specific row.
    # Actually, the most useful format for downstream analysis is:
    # Row 0: Summary (Observed Stat, P-val, etc.)
    # Rows 1..N: Null distribution values.
    # But TSV parsers might choke on mixed types if not careful.
    # Let's go with a standard format:
    # Columns: 'type', 'value', 'metadata'
    # type='observed', value=stat, metadata=p_val
    # type='null', value=sample, metadata=sample_id

    # Alternative: Save two logical sections.
    # Let's stick to a clean DataFrame where we store the null distribution
    # and append the observed stat as a specific row or save it as a separate metadata file?
    # The task says "Save ... to `data/results/permutation_results.tsv`".
    # We will save the null distribution values and the observed statistic.

    results_data = []

    # Add observed result
    results_data.append({
        "type": "observed",
        "value": observed_stat,
        "p_value": p_val_perm,
        "n_permutations": n_permutations,
        "seed": seed
    })

    # Add null distribution
    for i, val in enumerate(null_distribution):
        results_data.append({
            "type": "null",
            "value": float(val),
            "p_value": None,
            "n_permutations": None,
            "seed": None,
            "index": i
        })

    df = pd.DataFrame(results_data)

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save to TSV
    df.to_csv(output_path, sep="\t", index=False)
    logger.info(f"Saved permutation results to {output_path}")

def main():
    """Entry point for the script."""
    logger = setup_logger("analysis")
    try:
        save_permutation_results()
        logger.info("Task T034 completed successfully.")
    except Exception as e:
        logger.error(f"Task T034 failed: {e}")
        raise

if __name__ == "__main__":
    main()
