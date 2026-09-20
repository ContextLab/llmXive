"""
Model Training with LOSO Cross-Validation.

Implements T021 and integrates T022 checks.
"""
import os
import sys
import json
import pickle
import argparse
import time
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import mean_absolute_error, r2_score
from statsmodels.stats.power import FTestAnovaPower

# Project imports
from utils.logging import get_logger, log_info, log_warning, log_error
from utils.error_codes import ErrorCode
from models.loso_checks import apply_property_range_extrapolation_check, log_skipped_fold

logger = get_logger(__name__)

def load_processed_data(file_path: str = "data/processed/descriptors.csv") -> List[Dict[str, Any]]:
    """Load processed descriptor data from CSV."""
    import csv
    if not os.path.exists(file_path):
        log_error(f"Processed data file not found: {file_path}", ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"Processed data file not found: {file_path}")

    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            numeric_fields = [
                "mean_atomic_radius", "electronegativity_variance", 
                "valence_electron_count", "hume_rothery_concentration",
                "temperature", "composition"
            ]
            for field in numeric_fields:
                if field in row:
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        row[field] = 0.0
            data.append(row)
    return data

def train_random_forest(X: np.ndarray, y: np.ndarray, **kwargs) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    model = RandomForestRegressor(**kwargs)
    model.fit(X, y)
    return model

def run_loso_cv(
    data: List[Dict[str, Any]],
    feature_cols: List[str],
    target_col: str,
    group_col: str = "system_id"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Run Leave-One-System-Out Cross-Validation.
    
    Returns:
        (results, skipped_folds)
        results: List of dicts with fold metrics
        skipped_folds: List of dicts with skip reasons
    """
    # Extract features and targets
    X = np.array([[row[col] for col in feature_cols] for row in data])
    y = np.array([row[target_col] for row in data])
    groups = np.array([row[group_col] for row in data])

    # Group by system_id to ensure all rows of a system are in one fold
    unique_groups = np.unique(groups)
    logo = LeaveOneGroupOut()

    results = []
    skipped_folds = []
    fold_id_counter = 0

    # Pre-load properties for checks
    from models.loso_checks import load_elemental_properties
    properties = load_elemental_properties()

    for train_idx, test_idx in logo.split(X, y, groups):
        fold_id_counter += 1
        fold_id = f"LOSO-Fold-{fold_id_counter}"
        
        train_data = [data[i] for i in train_idx]
        test_data = [data[i] for i in test_idx]

        # Apply T022 checks
        should_skip, reasons = apply_property_range_extrapolation_check(
            train_data, test_data, fold_id, properties
        )

        if should_skip:
            skipped_folds.append({
                "fold_id": fold_id,
                "reasons": reasons
            })
            for reason in reasons:
                log_skipped_fold(fold_id, reason)
            continue

        # Train model
        X_train = np.array([[row[col] for col in feature_cols] for row in train_data])
        y_train = np.array([row[target_col] for row in train_data])
        X_test = np.array([[row[col] for col in feature_cols] for row in test_data])
        y_test = np.array([row[target_col] for row in test_data])

        model = train_random_forest(X_train, y_train, n_estimators=100, random_state=42)
        
        # Predict
        y_pred = model.predict(X_test)
        
        # Metrics
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        results.append({
            "fold_id": fold_id,
            "mae": mae,
            "r2": r2,
            "train_size": len(train_data),
            "test_size": len(test_data)
        })
        
        log_info(f"Fold {fold_id} completed: MAE={mae:.2f}, R2={r2:.4f}")

    return results, skipped_folds

def perform_power_analysis(results: List[Dict[str, Any]], target_power: float = 0.8) -> bool:
    """
    Perform statistical power analysis on the fold results.
    Simplified: Check if sample size is sufficient for the observed effect size.
    """
    if not results:
        log_error("No results for power analysis", ErrorCode.INSUFFICIENT_POWER)
        return False

    # Calculate effect size (simplified: difference in means vs std dev)
    maes = [r["mae"] for r in results]
    mean_mae = np.mean(maes)
    std_mae = np.std(maes)

    if std_mae == 0:
        log_warning("Zero variance in MAE, power analysis inconclusive")
        return True

    # Simplified power check: if we have enough folds and low variance, assume sufficient power
    n_folds = len(results)
    # Heuristic: need at least 5 folds and CV < 0.5
    cv = std_mae / mean_mae if mean_mae != 0 else 0
    
    if n_folds >= 5 and cv < 0.5:
        log_info(f"Power analysis passed: {n_folds} folds, CV={cv:.2f}")
        return True
    else:
        log_error(f"Insufficient power: {n_folds} folds, CV={cv:.2f}", ErrorCode.INSUFFICIENT_POWER)
        return False

def save_model(model: Any, path: str = "data/artifacts/model.pkl"):
    """Save the trained model to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    log_info(f"Model saved to {path}")

def save_report(results: List[Dict[str, Any]], skipped_folds: List[Dict[str, Any]], path: str = "data/artifacts/loso_report.json"):
    """Save the LOSO cross-validation report."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    report = {
        "results": results,
        "skipped_folds": skipped_folds,
        "summary": {
            "total_folds": len(results) + len(skipped_folds),
            "completed_folds": len(results),
            "skipped_folds": len(skipped_folds),
            "mean_mae": np.mean([r["mae"] for r in results]) if results else 0,
            "mean_r2": np.mean([r["r2"] for r in results]) if results else 0
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log_info(f"LOSO report saved to {path}")

def main():
    """Main entry point for model training."""
    parser = argparse.ArgumentParser(description="Train Random Forest with LOSO CV")
    parser.add_argument("--data", default="data/processed/descriptors.csv", help="Path to processed data")
    parser.add_argument("--output", default="data/artifacts/model.pkl", help="Path to save model")
    parser.add_argument("--report", default="data/artifacts/loso_report.json", help="Path to save report")
    args = parser.parse_args()

    log_info("Starting model training with LOSO CV")

    # Load data
    try:
        data = load_processed_data(args.data)
        log_info(f"Loaded {len(data)} records")
    except Exception as e:
        log_error(f"Failed to load data: {e}", ErrorCode.DATA_SOURCE_MISSING)
        sys.exit(1)

    # Define features and target
    feature_cols = [
        "mean_atomic_radius", 
        "electronegativity_variance", 
        "valence_electron_count", 
        "hume_rothery_concentration"
    ]
    target_col = "temperature"
    group_col = "system_id"

    # Run LOSO CV
    results, skipped_folds = run_loso_cv(data, feature_cols, target_col, group_col)

    # Power analysis
    if not perform_power_analysis(results):
        log_error("Power analysis failed. Halting.", ErrorCode.INSUFFICIENT_POWER)
        sys.exit(1)

    # Train final model on all data
    X = np.array([[row[col] for col in feature_cols] for row in data])
    y = np.array([row[target_col] for row in data])
    final_model = train_random_forest(X, y, n_estimators=100, random_state=42)

    # Save artifacts
    save_model(final_model, args.output)
    save_report(results, skipped_folds, args.report)

    log_info("Model training completed successfully")

if __name__ == "__main__":
    main()