import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np
import pandas as pd
from scipy import stats

def load_metrics(metrics_file: str) -> pd.DataFrame:
    """Loads metrics from a CSV file."""
    try:
        return pd.read_csv(metrics_file)
    except FileNotFoundError:
        logging.error(f"Metrics file not found: {metrics_file}")
        raise

def load_excluded_participants(exclusion_log: str) -> Set[str]:
    """Loads excluded participant IDs from a log file."""
    try:
        with open(exclusion_log, "r") as f:
            return set([line.strip() for line in f])
    except FileNotFoundError:
        logging.warning(f"Exclusion log not found: {exclusion_log}")
        return set()

def filter_participants(metrics_df: pd.DataFrame, excluded_ids: Set[str]) -> pd.DataFrame:
    """Filters out excluded participants from the metrics DataFrame."""
    return metrics_df[~metrics_df["participant_id"].isin(excluded_ids)]

def check_normality(data: np.ndarray) -> bool:
    """Checks if data is normally distributed using Shapiro-Wilk test."""
    _, p = stats.shapiro(data)
    return p > 0.05  # Assuming alpha=0.05

def perform_paired_ttest(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Performs a paired t-test and returns p-value and Cohen's d."""
    t_statistic, p_value = stats.ttest_rel(x, y)
    cohens_d = (np.mean(x) - np.mean(y)) / np.std(x - y)
    return p_value, cohens_d

def load_metrics_for_comparison(metrics_file: str, condition1: str, condition2: str) -> Tuple[np.ndarray, np.ndarray]:
    """Loads metrics for two conditions."""
    df = load_metrics(metrics_file)
    return df[condition1].values, df[condition2].values

def apply_fdr_correction(p_values: List[float]) -> List[float]:
    """Applies FDR correction using Benjamini-Hochberg."""
    from statsmodels.stats.multicomp import multipletests
    reject, pvals_corrected, _, _ = multipletests(p_values, method='fdr_bh')
    return list(pvals_corrected)

def run_mixed_effects_model(data: pd.DataFrame, fixed_effect: str, random_effect: str):
      """Placeholder for mixed-effects model implementation."""
      logging.warning("Mixed effects model not fully implemented")
      pass  # Replace with actual model fitting code

def run_cluster_based_permutation_test(data: np.ndarray):
    """Placeholder for permutation test implementation."""
    logging.warning("Permutation tests are currently unimplemented.")
    pass


def save_statistics_results(results: Dict, output_file: str) -> None:
    """Saves statistics results to a JSON file."""
    with open(output_file, "w") as f:
        json.dump(results, f, indent=4)

def calculate_cohens_d_and_ci(x: np.ndarray, y: np.ndarray):
      """Calculate Cohen's d effect size and confidence interval."""
      from statsmodels.stats.weightstats import ttest_ind
      t_stat, p_value = ttest_ind(x,y)

      # Calculate Cohen's d
      cohens_d = (np.mean(x) - np.mean(y)) / np.std(np.concatenate((x, y)))
      return cohens_d,p_value

def run_stats_pipeline():
    """Main function to run the statistics pipeline."""
    metrics_file = "results/metrics.csv"
    exclusion_log = "data/processed/rejected_participants.log"

    excluded_ids = load_excluded_participants(exclusion_log)
    metrics_df = load_metrics(metrics_file)
    filtered_df = filter_participants(metrics_df, excluded_ids)

    # Example: Compare amplitude at Fz for standard and deviant conditions
    try:
        standard_amplitude, deviant_amplitude = load_metrics_for_comparison(metrics_file, "standard_amplitude", "deviant_amplitude")
        p_value, cohens_d = perform_paired_ttest(standard_amplitude, deviant_amplitude)

        # Apply FDR correction
        corrected_p_value = apply_fdr_correction([p_value])[0]  # Corrected p-value for one comparison

        results = {
            "standard_amplitude_vs_deviant_amplitude": {
                "p_value": p_value,
                "cohens_d": cohens_d,
                "corrected_p_value": corrected_p_value
            }
        }

        save_statistics_results(results, "results/statistics.json")
    except Exception as e:
        logging.error(f"Error processing data: {e}")

if __name__ == "__main__":
    run_stats_pipeline()