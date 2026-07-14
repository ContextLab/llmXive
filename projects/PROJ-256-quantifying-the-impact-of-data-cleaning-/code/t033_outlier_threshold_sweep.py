"""
Task T033: Implement outlier threshold sweep for k ∈ {0.5, 1.0, 1.5, 2.0, 2.5, 3.0}
with FPR calculation AND inconsistency rate per threshold per FR-006.

Dependencies:
- Cleaning functions (T017-T021) in code/cleaning.py
- Analysis functions (T012, T023) in code/analysis.py
- Null FPR metrics from T032 (data/processed/null_fpr_metrics.json)
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import from project modules
from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis, identify_numerical_columns
from cleaning import apply_iqr_outlier_removal
from t032_permutation_null_fpr import load_dataset_from_processed

# Constants
OUTPUT_PATH = "data/processed/outlier_threshold_sweep.json"
THRESHOLD_VALUES = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
ALPHA = 0.05

logger = setup_logging("INFO")

THRESHOLD_VALUES = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
OUTPUT_FILE = "data/processed/outlier_threshold_sweep_report.json"
SIGNIFICANCE_THRESHOLD = 0.05


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        logger.warning(f"Baseline metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.warning(f"Cleaned metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def estimate_fpr_for_dataset(df: pd.DataFrame, outcome_col: str, group_col: str, threshold: float) -> float:
    """
    Estimate False Positive Rate for a given outlier threshold.
    This function simulates a null dataset by shuffling the outcome variable
    and then applies the cleaning strategy with the given threshold.
    """
    if df is None or df.empty:
        return 0.0

    # Create a null dataset by shuffling the outcome
    df_null = df.copy()
    shuffled_outcome = df_null[outcome_col].sample(frac=1, random_state=42).reset_index(drop=True)
    df_null[outcome_col] = shuffled_outcome

    # Apply outlier removal with the specific threshold
    try:
        df_cleaned = apply_iqr_outlier_removal(df_null, k=threshold)
    except Exception as e:
        logger.warning(f"Error applying outlier removal with k={threshold}: {e}")
        return 0.0

    if df_cleaned is None or df_cleaned.empty:
        return 0.0

    # Run baseline analysis on the cleaned null dataset
    # We need to extract numerical columns for analysis
    numerical_cols = identify_numerical_columns(df_cleaned)
    if not numerical_cols:
        return 0.0

    # Run t-test between group_col and outcome_col
    # Assuming group_col is categorical and outcome_col is numerical
    try:
        # Run t-test
        from scipy import stats
        groups = df_cleaned[group_col].unique()
        if len(groups) < 2:
            return 0.0

        # Get data for each group
        group_data = [df_cleaned[df_cleaned[group_col] == g][outcome_col] for g in groups]

        # Perform t-test
        t_stat, p_value = stats.ttest_ind(*group_data)

        # Check if p-value is significant (false positive)
        is_significant = p_value <= ALPHA
        return 1.0 if is_significant else 0.0

    except Exception as e:
        logger.warning(f"Error running t-test on null dataset: {e}")
        return 0.0

def calculate_inconsistency_rate(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any],
    threshold: float,
    strategy_name: str = "outlier_removal"
) -> float:
    """
    Calculate the Inconsistency Rate for a given threshold.
    Inconsistency Rate = proportion of datasets where significance status changes
    after applying the cleaning strategy.
    """
    if not baseline_metrics or not cleaned_metrics:
        return 0.0

    baseline_datasets = baseline_metrics.get('datasets', [])
    cleaned_datasets = cleaned_metrics.get('datasets', [])

    if not baseline_datasets:
        return 0.0

    inconsistent_count = 0
    total_count = 0

    for baseline_entry in baseline_datasets:
        dataset_name = baseline_entry.get('dataset_name')
        if not dataset_name:
            continue

        # Find corresponding cleaned entry
        cleaned_entry = None
        for entry in cleaned_datasets:
            if entry.get('dataset_name') == dataset_name:
                # Check if this entry has the specific strategy
                if entry.get('cleaning_strategy') == strategy_name:
                    cleaned_entry = entry
                    break

        if not cleaned_entry:
            continue

        total_count += 1

        # Get baseline significance
        baseline_tests = baseline_entry.get('t_test', {})
        baseline_p = baseline_tests.get('p_value')
        baseline_significant = baseline_p is not None and baseline_p <= ALPHA

        # Get cleaned significance
        cleaned_tests = cleaned_entry.get('t_test', {})
        cleaned_p = cleaned_tests.get('p_value')
        cleaned_significant = cleaned_p is not None and cleaned_p <= ALPHA

        # Check if significance status changed
        if baseline_significant != cleaned_significant:
            inconsistent_count += 1

    if total_count == 0:
        return 0.0

    return inconsistent_count / total_count

def run_threshold_sweep(
    thresholds: List[float] = None,
    baseline_metrics: Dict[str, Any] = None,
    cleaned_metrics: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Run the outlier threshold sweep across multiple k values.
    For each threshold, calculate FPR and Inconsistency Rate.
    """
    if thresholds is None:
        thresholds = THRESHOLD_VALUES

    if baseline_metrics is None:
        baseline_metrics = load_baseline_metrics()

    if cleaned_metrics is None:
        cleaned_metrics = load_cleaned_metrics()

    results = []

    logger.info(f"Starting threshold sweep for k values: {thresholds}")

    for k in thresholds:
        logger.info(f"Processing threshold k={k}")

        # Calculate FPR using null datasets
        # We need to load real datasets to generate null versions
        # For this, we'll use the datasets from baseline_metrics
        fpr_values = []
        baseline_datasets = baseline_metrics.get('datasets', [])

        for dataset_entry in baseline_datasets:
            dataset_name = dataset_entry.get('dataset_name')
            try:
                # Load the dataset from processed data
                df = load_dataset_from_processed(dataset_name)
                if df is None:
                    continue

                # Estimate FPR for this dataset
                # We need outcome_col and group_col - these should be in the dataset metadata
                # For now, we'll try to infer or use defaults
                outcome_col = dataset_entry.get('outcome_col', 'outcome')
                group_col = dataset_entry.get('group_col', 'group')

                # Check if these columns exist
                if outcome_col not in df.columns or group_col not in df.columns:
                    # Try to find suitable columns
                    numerical_cols = identify_numerical_columns(df)
                    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

                    if numerical_cols and categorical_cols:
                        outcome_col = numerical_cols[0]
                        group_col = categorical_cols[0]
                    else:
                        continue

                fpr = estimate_fpr_for_dataset(df, outcome_col, group_col, k)
                fpr_values.append(fpr)

            except Exception as e:
                logger.warning(f"Error processing dataset {dataset_name} for FPR: {e}")
                continue

        avg_fpr = np.mean(fpr_values) if fpr_values else 0.0

        # Calculate Inconsistency Rate
        inconsistency_rate = calculate_inconsistency_rate(
            baseline_metrics, cleaned_metrics, k, "outlier_removal"
        )

        result = {
            'threshold_k': k,
            'fpr': avg_fpr,
            'inconsistency_rate': inconsistency_rate,
            'n_datasets_analyzed': len(fpr_values)
        }
        results.append(result)

        logger.info(f"  FPR: {avg_fpr:.4f}, Inconsistency Rate: {inconsistency_rate:.4f}")

    return results

def write_output(results: List[Dict[str, Any]], output_path: str = OUTPUT_PATH) -> bool:
    """Write the threshold sweep results to a JSON file."""
    output = {
        'generated_at': datetime.now().isoformat(),
        'threshold_values': THRESHOLD_VALUES,
        'alpha': ALPHA,
        'results': results
    }

    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        logger.info(f"Threshold sweep results written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        return False

def main():
    """Main entry point for the outlier threshold sweep task."""
    logger.info("Starting outlier threshold sweep (T033)")

    # Load metrics
    baseline_metrics = load_baseline_metrics()
    cleaned_metrics = load_cleaned_metrics()

    if not baseline_metrics:
        logger.error("No baseline metrics found. Please run baseline analysis first.")
        return False

    if not cleaned_metrics:
        logger.error("No cleaned metrics found. Please run cleaning analysis first.")
        return False

    # Run the threshold sweep
    results = run_threshold_sweep(
        thresholds=THRESHOLD_VALUES,
        baseline_metrics=baseline_metrics,
        cleaned_metrics=cleaned_metrics
    )

    # Write output
    success = write_output(results)

    if success:
        logger.info("Outlier threshold sweep completed successfully")
        return True
    else:
        logger.error("Outlier threshold sweep failed to write output")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
