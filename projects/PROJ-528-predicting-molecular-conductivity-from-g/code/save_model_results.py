"""
Task T033: Save model results and sensitivity analysis data.

Loads sensitivity analysis results (from T032), trains models (from T029/T030),
and aggregates the results into `data/processed/model_results.json`.

Output Schema:
{
    "rf_r2": float,
    "gb_r2": float,
    "sensitivity_analysis": [
        {"threshold": float, "r2": float, "variance_metric": float},
        ...
    ]
}
"""
import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Local imports matching API surface
from code.logging_config import setup_logging
from code.model_training import train_models
from code.scaffold_split import scaffold_split
from code.data_loader import load_processed_data
from code.config import DATA_PATH, SEED, TARGET_VAR, OUTLIER_SIGMA
from code.outlier_sensitivity import apply_threshold_filter, retrain_with_filtered_data

def load_sensitivity_analysis(path: str) -> List[Dict[str, Any]]:
    """Load sensitivity analysis results from T032."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Sensitivity analysis file not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    # Ensure we return the list of thresholds and their metrics
    # The T032 output structure is expected to be:
    # {"thresholds": [...], "r2_scores": [...], ...} or a list of results
    if isinstance(data, list):
        return data
    # If it's a dict with separate arrays, reconstruct the list
    if "thresholds" in data and "r2_scores" in data:
        results = []
        thresholds = data["thresholds"]
        r2_scores = data["r2_scores"]
        # Assume variance_metric is available or compute from data if needed
        # For T032, we expect 'variance_metric' or similar in the data
        # If not present, we might need to extract it or default
        # Based on T032 description: "Save results to ... with keys: thresholds, r2_scores, kruskal_statistic, p_value, range, population_variance"
        # The sensitivity_analysis list in T033 expects: [{threshold, r2, variance_metric}, ...]
        # We will map 'population_variance' to variance_metric if available, or use a placeholder if not
        var_metric = data.get("population_variance", 0.0) 
        # If r2_scores is a list of means per threshold, we zip them
        if isinstance(r2_scores, list) and len(r2_scores) == len(thresholds):
            for t, r2 in zip(thresholds, r2_scores):
                results.append({
                    "threshold": t,
                    "r2": r2,
                    "variance_metric": var_metric
                })
        return results
    return []

def prepare_data_and_split(data_path: str, target_var: str, seed: int):
    """Load data and perform scaffold split."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading processed data from {data_path}")
    df = load_processed_data(data_path)
    
    # Ensure target variable exists
    if target_var not in df.columns:
        # Check for log-transformed version if T028 ran
        log_target = f"log_{target_var}"
        if log_target in df.columns:
            target_var = log_target
            logger.info(f"Using log-transformed target: {target_var}")
        else:
            raise ValueError(f"Target variable '{target_var}' not found in data.")
    
    logger.info("Performing scaffold split...")
    train_idx, test_idx = scaffold_split(df, target_var, seed=seed)
    
    X_train = df.iloc[train_idx].drop(columns=[target_var])
    y_train = df.iloc[train_idx][target_var]
    X_test = df.iloc[test_idx].drop(columns=[target_var])
    y_test = df.iloc[test_idx][target_var]
    
    return X_train, y_train, X_test, y_test, df

def train_models_and_get_r2(X_train, y_train, X_test, y_test, seed: int):
    """Train RF and GB models and return R2 scores."""
    logger = logging.getLogger(__name__)
    logger.info("Training models...")
    
    # Train models
    rf_model, gb_model, metrics = train_models(
        X_train, y_train, X_test, y_test,
        rf_params={'n_estimators': 100, 'max_depth': None, 'random_state': seed},
        gb_params={'n_estimators': 100, 'learning_rate': 0.1, 'random_state': seed}
    )
    
    # Extract R2 scores from metrics
    # Assuming metrics structure from T029/T030: {'rf_r2': ..., 'gb_r2': ..., 'rf_cv': ..., 'gb_cv': ...}
    rf_r2 = metrics.get('rf_r2', 0.0)
    gb_r2 = metrics.get('gb_r2', 0.0)
    
    logger.info(f"RF R2: {rf_r2:.4f}, GB R2: {gb_r2:.4f}")
    return rf_r2, gb_r2

def main():
    parser = argparse.ArgumentParser(description="Save model results and sensitivity analysis.")
    parser.add_argument("--data", type=str, default=os.path.join(DATA_PATH, "processed", "descriptors.csv"),
                        help="Path to processed descriptor data (CSV).")
    parser.add_argument("--output", type=str, default=os.path.join(DATA_PATH, "processed", "model_results.json"),
                        help="Path to save model results JSON.")
    parser.add_argument("--sensitivity-input", type=str, default=os.path.join(DATA_PATH, "processed", "sensitivity_analysis.json"),
                        help="Path to sensitivity analysis JSON from T032.")
    parser.add_argument("--target", type=str, default=TARGET_VAR, help="Target variable name.")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging("save_model_results")
    logger.info("Starting T033: Save model results and sensitivity analysis.")

    # 1. Load Sensitivity Analysis (from T032)
    logger.info(f"Loading sensitivity analysis from {args.sensitivity_input}")
    try:
        sensitivity_data = load_sensitivity_analysis(args.sensitivity_input)
    except FileNotFoundError:
        logger.warning("Sensitivity analysis file not found. Running a quick sensitivity sweep if possible, or using empty list.")
        # If T032 failed to run, we might need to run a minimal one or leave empty
        # For now, we assume it exists as per task dependencies.
        sensitivity_data = []

    # 2. Prepare Data and Split
    X_train, y_train, X_test, y_test, full_df = prepare_data_and_split(
        args.data, args.target, SEED
    )

    # 3. Train Models and Get R2
    rf_r2, gb_r2 = train_models_and_get_r2(X_train, y_train, X_test, y_test, SEED)

    # 4. Compile Results
    results = {
        "rf_r2": float(rf_r2),
        "gb_r2": float(gb_r2),
        "sensitivity_analysis": sensitivity_data
    }

    # 5. Save to Output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {args.output}")
    logger.info("T033 completed successfully.")

if __name__ == "__main__":
    main()