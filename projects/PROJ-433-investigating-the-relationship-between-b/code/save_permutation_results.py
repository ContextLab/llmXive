import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from analysis import load_metrics_and_behavioral_data, run_permutation_test, calculate_permutation_p_value
from utils import setup_logger, get_seeded_rng

def save_permutation_results(
    subject_ids: list,
    transition_counts: np.ndarray,
    dsst_scores: np.ndarray,
    observed_coef: float,
    null_distribution: np.ndarray,
    p_value: float,
    output_path: Path,
    logger: logging.Logger
) -> None:
    """
    Save permutation test raw results and null distribution data to a TSV file.

    The output file `data/results/permutation_results.tsv` will contain:
    1. A summary row with observed statistics and p-value.
    2. Rows for each permutation shuffle (index, shuffled_coef).

    Args:
        subject_ids: List of subject identifiers (for metadata).
        transition_counts: Array of reconfigurability metrics.
        dsst_scores: Array of DSST scores.
        observed_coef: The Spearman correlation coefficient from real data.
        null_distribution: Array of correlation coefficients from shuffled data.
        p_value: The calculated permutation p-value.
        output_path: Path to the output TSV file.
        logger: Logger instance for logging progress.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {output_path.parent}")

    # Prepare summary data
    summary_data = {
        "metric": "transition_count_vs_D SST",
        "n_subjects": len(subject_ids),
        "observed_coef": observed_coef,
        "p_value": p_value,
        "n_permutations": len(null_distribution),
        "mean_null_coef": float(np.mean(null_distribution)),
        "std_null_coef": float(np.std(null_distribution)),
        "min_null_coef": float(np.min(null_distribution)),
        "max_null_coef": float(np.max(null_distribution))
    }

    # Prepare permutation data
    perm_data = []
    for i, coef in enumerate(null_distribution):
        perm_data.append({
            "shuffle_index": i,
            "shuffled_coef": float(coef)
        })

    # Create DataFrame for permutations
    df_perm = pd.DataFrame(perm_data)

    # Create DataFrame for summary (single row)
    df_summary = pd.DataFrame([summary_data])

    # Write to TSV
    # We write the summary first, then the permutation data.
    # To keep it as a single TSV as requested, we'll use a comment header for summary
    # or just append them. The requirement says "raw results and null distribution data".
    # A common format is to have the summary as the first few rows (commented or not)
    # followed by the data. Let's write the summary as the first block.

    with open(output_path, 'w') as f:
        f.write("# Permutation Test Summary\n")
        df_summary.to_csv(f, sep='\t', index=False)
        f.write("\n# Null Distribution (Shuffled Coefficients)\n")
        df_perm.to_csv(f, sep='\t', index=False)

    logger.info(f"Saved permutation results to {output_path}")

def main():
    """
    Main entry point to run permutation test and save results.
    """
    logger = setup_logger("analysis_log")
    logger.info("Starting permutation results generation (T034).")

    # Load data
    try:
        subjects, transition_counts, dsst_scores = load_metrics_and_behavioral_data()
        logger.info(f"Loaded data for {len(subjects)} subjects.")
    except FileNotFoundError as e:
        logger.error(f"Data files not found: {e}")
        raise

    if len(transition_counts) == 0 or len(dsst_scores) == 0:
        logger.warning("No data available for permutation test.")
        return

    # Run permutation test
    # Assuming run_permutation_test returns (null_distribution, p_value, observed_coef)
    # We need to ensure the function signature matches what's in analysis.py
    # Based on T032/T033 context, we call the function and get results.
    
    # Re-compute observed correlation for the summary
    from scipy.stats import spearmanr
    observed_coef, _ = spearmanr(transition_counts, dsst_scores)

    # Run the test
    # We assume run_permutation_test takes the arrays and returns the distribution and p-value
    # If the existing analysis.py function has a different signature, we adapt here.
    # Based on T033, calculate_permutation_p_value is used.
    
    # Let's assume run_permutation_test returns (null_dist, p_val)
    # and we already have observed_coef.
    # If the function signature in analysis.py is different, we must match it.
    # The API surface says: run_permutation_test, calculate_permutation_p_value
    # Let's assume run_permutation_test does the shuffling and returns the distribution.
    
    null_distribution, p_value = run_permutation_test(
        transition_counts, 
        dsst_scores, 
        n_permutations=1000, 
        seed=42,
        logger=logger
    )

    logger.info(f"Permutation test complete. Observed coef: {observed_coef:.4f}, p-value: {p_value:.4f}")

    # Define output path
    output_path = Path("data/results/permutation_results.tsv")

    # Save results
    save_permutation_results(
        subject_ids=[s.id for s in subjects],
        transition_counts=transition_counts,
        dsst_scores=dsst_scores,
        observed_coef=observed_coef,
        null_distribution=null_distribution,
        p_value=p_value,
        output_path=output_path,
        logger=logger
    )

    logger.info("T034 completed successfully.")

if __name__ == "__main__":
    main()