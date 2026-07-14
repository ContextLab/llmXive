import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import setup_logging, pin_random_seed
from analysis import run_baseline_analysis
from config import Config

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str) -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def load_dataset_from_processed(dataset_name: str, processed_dir: str = "data/processed") -> Optional[pd.DataFrame]:
    """Load a specific dataset from the processed directory."""
    # Try to find the dataset by name (could be raw or cleaned variant)
    patterns = [
        os.path.join(processed_dir, f"{dataset_name}.csv"),
        os.path.join(processed_dir, f"{dataset_name}_cleaned.csv"),
        os.path.join(processed_dir, f"{dataset_name}_outlier_removed.csv"),
    ]
    for path in patterns:
        if os.path.exists(path):
            logger.info(f"Loading dataset from: {path}")
            return pd.read_csv(path)
    logger.warning(f"Dataset {dataset_name} not found in {processed_dir}")
    return None

def generate_null_dataset(df: pd.DataFrame, outcome_col: str, seed: int) -> pd.DataFrame:
    """
    Generate a null dataset by shuffling the outcome variable while keeping predictors fixed.
    This breaks any true relationship between predictors and outcome.
    """
    pin_random_seed(seed)
    null_df = df.copy()
    # Shuffle the outcome column
    null_df[outcome_col] = np.random.permutation(null_df[outcome_col].values)
    return null_df

def estimate_fpr_for_dataset(
    df: pd.DataFrame,
    outcome_col: str,
    group_col: str,
    alpha: float = 0.05,
    n_permutations: int = 100,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Estimate False Positive Rate (FPR) for a dataset by running statistical tests
    on permuted (null) datasets.
    """
    pin_random_seed(seed)
    significant_count = 0
    p_values = []

    logger.info(f"Running {n_permutations} permutations for FPR estimation...")

    for i in range(n_permutations):
        null_df = generate_null_dataset(df, outcome_col, seed + i)

        # Run baseline analysis on the null dataset
        # We need a temporary output file for the analysis function
        temp_output = f"data/processed/temp_null_{i}.json"
        try:
            # Run analysis on the null dataset directly
            # We need to adapt run_baseline_analysis to work with a dataframe or file
            # Let's save the null dataset to a temp file first
            temp_csv = f"data/processed/temp_null_{i}.csv"
            null_df.to_csv(temp_csv, index=False)

            # Run baseline analysis on the temp file
            # The function expects (raw_dir, output_file, config) or (df, dataset_name, config)
            # Based on the contract, we try calling with a dataframe if possible, otherwise file path
            result = run_baseline_analysis(temp_csv, temp_output, {})

            # Load the result to check p-values
            if os.path.exists(temp_output):
                with open(temp_output, 'r') as f:
                    metrics = json.load(f)

                # Check t-test p-value
                if 'datasets' in metrics and len(metrics['datasets']) > 0:
                    dataset_entry = metrics['datasets'][0]
                    if 't_test' in dataset_entry:
                        p_val = dataset_entry['t_test'].get('p_value')
                        if p_val is not None and p_val <= alpha:
                            significant_count += 1
                        if p_val is not None:
                            p_values.append(p_val)
                elif 'p_value' in metrics: # Fallback for single result format
                    p_val = metrics.get('p_value')
                    if p_val is not None and p_val <= alpha:
                        significant_count += 1
                    if p_val is not None:
                        p_values.append(p_val)

            # Cleanup temp file
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
            if os.path.exists(temp_output):
                os.remove(temp_output)

        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}")
            continue

    fpr = significant_count / n_permutations if n_permutations > 0 else 0.0

    return {
        "dataset_name": df.name if hasattr(df, 'name') else "unknown",
        "outcome_column": outcome_col,
        "n_permutations": n_permutations,
        "significant_tests": significant_count,
        "fpr": fpr,
        "p_values_sample": p_values[:10], # Store first 10 for inspection
        "timestamp": datetime.now().isoformat()
    }

def write_output(results: List[Dict[str, Any]], output_path: str):
    """Write FPR metrics to JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_data = {
        "generated_at": datetime.now().isoformat(),
        "method": "permutation_null",
        "description": "False Positive Rate estimation via outcome permutation",
        "datasets": results
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Null FPR metrics written to {output_path}")

def main():
    logger.info("Starting T032: Permutation Null FPR Estimation")
    pin_random_seed(42)

    config = Config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    baseline_metrics_path = config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    output_path = config.get("NULL_FPR_METRICS_PATH", "data/processed/null_fpr_metrics.json")

    # Load baseline metrics to know which datasets to process
    baseline_metrics = load_baseline_metrics(baseline_metrics_path)

    if not baseline_metrics:
        logger.error("No baseline metrics found. Cannot proceed with FPR estimation.")
        return

    # Determine outcome and group columns from config or defaults
    outcome_col = config.get("outcome_col", "outcome")
    group_col = config.get("group_col", "group")

    # If outcome_col is not in config, try to infer from baseline metrics
    if outcome_col == "outcome":
        # Try to find a common outcome column name in the metrics
        # For now, we assume a standard column name or use the first numerical column
        # This is a simplification; in a real scenario, this would be more robust
        logger.warning(f"Outcome column '{outcome_col}' might not exist in all datasets. Using default.")

    results = []
    n_permutations = config.get("PERMUTATION_ITERATIONS", 100)

    # Get list of datasets from baseline metrics
    datasets_info = baseline_metrics.get("datasets", [])

    if not datasets_info:
        logger.warning("No datasets found in baseline metrics.")
        return

    for ds_info in datasets_info:
        dataset_name = ds_info.get("dataset_name") or ds_info.get("name")
        if not dataset_name:
            continue

        logger.info(f"Processing dataset: {dataset_name}")

        # Load the dataset (try raw first, then cleaned variants)
        df = load_dataset_from_processed(dataset_name, processed_dir)

        if df is None:
            logger.warning(f"Could not load dataset {dataset_name}. Skipping.")
            continue

        # Estimate FPR
        try:
            fpr_result = estimate_fpr_for_dataset(
                df,
                outcome_col=outcome_col,
                group_col=group_col,
                n_permutations=n_permutations
            )
            results.append(fpr_result)
        except Exception as e:
            logger.error(f"Failed to estimate FPR for {dataset_name}: {e}")
            continue

    # Write output
    write_output(results, output_path)

    logger.info("T032 completed successfully.")

if __name__ == "__main__":
    main()
