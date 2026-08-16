"""
Null Baseline Comparison (T030c)

Implements:
1. Train a DummyRegressor (strategy='mean') on the training split.
2. Evaluate on the test set to obtain baseline R² and MAE.
3. Perform a paired t-test (scipy.stats.ttest_rel) on residuals of the selected model vs. baseline.
4. Report p-value and status (significant/not significant) in results/results.json.
"""
import argparse
import json
import logging
import os
import sys
import pickle
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.dummy import DummyRegressor
from sklearn.metrics import r2_score, mean_absolute_error

# Project root resolution
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def load_features():
    """Load features from data/processed/features.json."""
    path = os.path.join(DATA_PROCESSED_DIR, "features.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found: {path}")
    with open(path, "r") as f:
        data = json.load(f)
    return pd.DataFrame(data)

def load_rf_results():
    """Load model and split config to reconstruct residuals if needed,
    but primarily we read residuals.csv as per T029."""
    model_path = os.path.join(RESULTS_DIR, "model.pkl")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model

def calculate_mean_baseline_metrics(X_train, y_train, X_test, y_test):
    """
    Train DummyRegressor (mean strategy) and evaluate.
    Returns baseline R2, MAE, and predictions on test set.
    """
    logger.info("Training DummyRegressor (strategy='mean')...")
    dummy_model = DummyRegressor(strategy="mean")
    dummy_model.fit(X_train, y_train)

    logger.info("Evaluating DummyRegressor on test set...")
    y_pred_baseline = dummy_model.predict(X_test)
    baseline_r2 = r2_score(y_test, y_pred_baseline)
    baseline_mae = mean_absolute_error(y_test, y_pred_baseline)

    logger.info(f"Baseline R²: {baseline_r2:.4f}, Baseline MAE: {baseline_mae:.4f}")
    return baseline_r2, baseline_mae, y_pred_baseline

def compare_and_save_results(y_true, y_pred_model, y_pred_baseline, p_value_permutation):
    """
    Perform paired t-test on residuals of model vs baseline.
    Save results to results/results.json.
    """
    residuals_model = y_true - y_pred_model
    residuals_baseline = y_true - y_pred_baseline

    logger.info(f"Residuals Model (n={len(residuals_model)}), Mean: {np.mean(residuals_model):.4f}")
    logger.info(f"Residuals Baseline (n={len(residuals_baseline)}), Mean: {np.mean(residuals_baseline):.4f}")

    # Paired t-test
    t_stat, p_value_ttest = stats.ttest_rel(residuals_model, residuals_baseline)

    significance = "significant" if p_value_ttest < 0.05 else "not significant"
    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_value_ttest:.4f} -> {significance}")

    # Load existing results if present to merge
    results_path = os.path.join(RESULTS_DIR, "results.json")
    results = {}
    if os.path.exists(results_path):
        try:
            with open(results_path, "r") as f:
                results = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing results.json is invalid JSON, overwriting.")

    # Update with null baseline comparison results
    results["baseline_r2"] = float(results.get("baseline_r2", 0)) # Should be updated below
    results["p_value_ttest"] = float(p_value_ttest)
    results["t_test_status"] = significance
    results["p_value_permutation"] = float(p_value_permutation)

    # We need baseline_r2 specifically for this task, but it's not passed here directly.
    # We will update the caller to ensure it's passed or loaded.
    # For now, we assume the caller updates this field or we do a second pass.
    # Actually, let's calculate baseline_r2 inside this function if we have y_test.
    # But to keep signatures clean, let's assume the caller handles the update of baseline_r2.
    # Wait, the task requires writing baseline_r2 to results.json.
    # Let's refactor: The caller will pass baseline_r2.

    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {results_path}")
    return results

def parse_args():
    parser = argparse.ArgumentParser(description="Null Baseline Comparison (T030c)")
    parser.add_argument("--features", type=str, default=os.path.join(DATA_PROCESSED_DIR, "features.json"),
                        help="Path to features.json")
    parser.add_argument("--model", type=str, default=os.path.join(RESULTS_DIR, "model.pkl"),
                        help="Path to trained model")
    parser.add_argument("--residuals", type=str, default=os.path.join(DATA_PROCESSED_DIR, "residuals.csv"),
                        help="Path to residuals.csv (from T029)")
    parser.add_argument("--split-config", type=str, default=os.path.join(DATA_PROCESSED_DIR, "split_config.json"),
                        help="Path to split_config.json")
    return parser.parse_args()

def main():
    args = parse_args()

    logger.info("Loading features...")
    df = load_features()

    # Load split config to get train/test indices
    split_config_path = os.path.join(DATA_PROCESSED_DIR, "split_config.json")
    if not os.path.exists(split_config_path):
        raise FileNotFoundError(f"Split config not found: {split_config_path}")
    with open(split_config_path, "r") as f:
        split_config = json.load(f)

    # We need to reconstruct X_train, y_train, X_test, y_test
    # The features.json likely contains the full dataset with a 'split' column or similar.
    # Let's assume the split_config contains indices or a column name indicating split.
    # Based on T027a, it stores split indices.
    train_indices = split_config.get("train_indices", [])
    test_indices = split_config.get("test_indices", [])

    if not train_indices or not test_indices:
        # Fallback: try to find a 'split' column
        if "split" in df.columns:
            train_mask = df["split"] == "train"
            test_mask = df["split"] == "test"
            train_indices = df[train_mask].index.tolist()
            test_indices = df[test_mask].index.tolist()
        else:
            raise ValueError("Cannot determine train/test split from split_config or features.")

    # Assume target is 'fidelity_loss'
    target_col = "fidelity_loss"
    feature_cols = [c for c in df.columns if c != target_col and c != "split" and c != "sample_id"]

    X = df[feature_cols].values
    y = df[target_col].values

    X_train = X[train_indices]
    y_train = y[train_indices]
    X_test = X[test_indices]
    y_test = y[test_indices]

    logger.info(f"Train size: {len(y_train)}, Test size: {len(y_test)}")

    # Calculate Baseline Metrics
    baseline_r2, baseline_mae, y_pred_baseline = calculate_mean_baseline_metrics(X_train, y_train, X_test, y_test)

    # Load residuals from T029 to get model predictions vs true
    # T029 writes residuals.csv with columns: y_true, y_pred_model (or similar)
    residuals_path = args.residuals
    if not os.path.exists(residuals_path):
        raise FileNotFoundError(f"Residuals file not found: {residuals_path}")
    
    residuals_df = pd.read_csv(residuals_path)
    
    # Determine column names dynamically or assume standard
    if "y_true" in residuals_df.columns and "y_pred" in residuals_df.columns:
        y_true_res = residuals_df["y_true"].values
        y_pred_model_res = residuals_df["y_pred"].values
    elif "y_true" in residuals_df.columns and "y_pred_model" in residuals_df.columns:
        y_true_res = residuals_df["y_true"].values
        y_pred_model_res = residuals_df["y_pred_model"].values
    else:
        # Fallback: try to match length with test set
        if len(residuals_df) == len(y_test):
            # Assume first col is true, second is pred
            y_true_res = residuals_df.iloc[:, 0].values
            y_pred_model_res = residuals_df.iloc[:, 1].values
        else:
            raise ValueError("Cannot identify y_true and y_pred columns in residuals.csv")

    # Calculate baseline residuals for the test set
    # We need y_pred_baseline for the test set (already calculated above)
    # And y_true for the test set
    y_true_test = y_test
    y_pred_baseline_test = y_pred_baseline

    # Perform Paired T-Test on residuals
    # Residuals = y_true - y_pred
    residuals_model = y_true_test - y_pred_model_res
    residuals_baseline = y_true_test - y_pred_baseline_test

    logger.info(f"Running paired t-test on {len(residuals_model)} residuals...")
    t_stat, p_value_ttest = stats.ttest_rel(residuals_model, residuals_baseline)
    significance = "significant" if p_value_ttest < 0.05 else "not significant"
    logger.info(f"Paired t-test: t={t_stat:.4f}, p={p_value_ttest:.4f} -> {significance}")

    # Load permutation p-value from existing results (T029/T030a output)
    results_path = os.path.join(RESULTS_DIR, "results.json")
    p_value_permutation = 0.0
    if os.path.exists(results_path):
        try:
            with open(results_path, "r") as f:
                existing_results = json.load(f)
                p_value_permutation = existing_results.get("p_value_permutation", 0.0)
        except:
            pass

    # Save final results
    final_results = {
        "baseline_r2": float(baseline_r2),
        "baseline_mae": float(baseline_mae),
        "p_value_ttest": float(p_value_ttest),
        "t_test_status": significance,
        "p_value_permutation": float(p_value_permutation)
    }

    with open(results_path, "w") as f:
        json.dump(final_results, f, indent=2)

    logger.info(f"Final results saved to {results_path}")
    logger.info(f"Baseline R²: {baseline_r2:.4f}, T-Test Status: {significance}")

if __name__ == "__main__":
    main()