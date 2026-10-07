import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Local imports matching the API surface
from utils import get_logger, setup_logging, read_json, write_json
from config import ensure_directories

# Configuration
PERMUTATION_COUNT = 100
SEED = 42

def load_cleaned_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned dataset."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    return pd.read_csv(data_path)

def prepare_model_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare X (features) and y (target) for modeling.
    Returns: X, y, feature_names
    """
    target_col = 'MWQ_Score'
    feature_cols = ['Global_Signal_SD', 'Mean_FD', 'Mean_DVARS', 'Age']
    # Sex is categorical, handled separately if needed, but for simplicity here assume numeric encoding or drop
    if 'Sex' in df.columns:
        # Simple label encoding for binary Sex if needed, otherwise drop if not numeric
        if df['Sex'].dtype == object:
            df['Sex'] = df['Sex'].map({'M': 0, 'F': 1}).fillna(0)
        feature_cols.append('Sex')

    # Ensure columns exist
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
    if target_col not in df.columns:
        raise ValueError(f"Missing target column: {target_col}")

    X = df[feature_cols].values
    y = df[target_col].values
    return X, y, feature_cols

def run_ridge_regression_with_nested_cv(
    X: np.ndarray, y: np.ndarray, alpha_grid: List[float], cv_folds: int, seed: int
) -> Dict[str, Any]:
    """
    Run nested cross-validation for Ridge Regression.
    Outer loop: performance estimation
    Inner loop: alpha tuning
    """
    rng = np.random.RandomState(seed)
    outer_cv = KFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=seed) # Inner CV for tuning

    scores = []
    alphas_used = []
    residuals_list = []
    y_pred_list = []
    y_true_list = []

    scaler = StandardScaler()

    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Scale
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Inner CV for alpha tuning
        ridge_cv = RidgeCV(alphas=alpha_grid, cv=inner_cv, store_cv_values=True)
        ridge_cv.fit(X_train_scaled, y_train)

        best_alpha = ridge_cv.alpha_
        alphas_used.append(best_alpha)

        # Evaluate on outer test set
        y_pred = ridge_cv.predict(X_test_scaled)
        mse = np.mean((y_test - y_pred) ** 2)
        scores.append(mse)

        # Collect residuals and predictions for aggregation
        residuals_list.extend(y_test - y_pred)
        y_pred_list.extend(y_pred)
        y_true_list.extend(y_test)

    mean_mae = np.mean(np.abs(residuals_list)) # Using MAE as primary metric per task
    # Calculate Pearson r
    correlation = np.corrcoef(y_true_list, y_pred_list)[0, 1]
    # Calculate R2
    ss_res = np.sum((np.array(y_true_list) - np.array(y_pred_list)) ** 2)
    ss_tot = np.sum((np.array(y_true_list) - np.mean(y_true_list)) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    return {
        "mae": float(mean_mae),
        "r": float(correlation),
        "r2": float(r2),
        "alpha": float(np.mean(alphas_used)) if alphas_used else float(alpha_grid[0]),
        "residuals": residuals_list,
        "predictions": y_pred_list,
        "actuals": y_true_list
    }

def run_null_distribution_analysis(
    X: np.ndarray, y: np.ndarray, alpha_grid: List[float], cv_folds: int,
    n_permutations: int, seed: int
) -> List[Dict[str, float]]:
    """
    Run permutation test to generate null distribution.
    **T045 Implementation**: Verifies that exactly n_permutations are executed.
    """
    rng = np.random.RandomState(seed)
    results = []
    executed_count = 0

    for i in range(n_permutations):
        # Permute y
        y_permuted = y.copy()
        rng.shuffle(y_permuted)

        # Run the pipeline on permuted data
        # We use a simplified version of the nested CV here for speed in permutation loop
        # In a real heavy-duty scenario, we might parallelize, but we stick to the logic
        try:
            res = run_ridge_regression_with_nested_cv(X, y_permuted, alpha_grid, cv_folds, seed + i)
            results.append({
                "mae": res["mae"],
                "r2": res["r2"]
            })
            executed_count += 1
        except Exception as e:
            logging.error(f"Permutation {i} failed: {e}")
            # Do not count failed permutations as successful runs

    # T045: Verify Permutation Count
    if executed_count != n_permutations:
        raise RuntimeError(
            f"Permutation count mismatch: Expected {n_permutations}, but only {executed_count} completed. "
            "Invalid p-value calculation cannot proceed."
        )

    return results

def plot_null_distribution(null_results: List[Dict], observed_mae: float, output_path: str):
    """Plot the null distribution histogram."""
    null_maes = [r["mae"] for r in null_results]
    plt.figure(figsize=(10, 6))
    plt.hist(null_maes, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
    plt.axvline(observed_mae, color='red', linestyle='dashed', linewidth=2, label=f'Observed MAE: {observed_mae:.2f}')
    plt.xlabel('MAE (Null Distribution)')
    plt.ylabel('Frequency')
    plt.title('Null Distribution of MAE')
    plt.legend()
    plt.savefig(output_path)
    plt.close()

def main():
    """Main entry point for modeling pipeline."""
    logger = get_logger(__name__)
    setup_logging()

    # Parse arguments (simulated for script execution)
    data_path = "data/processed/cleaned_data.csv"
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--data" and i + 1 < len(sys.argv):
                data_path = sys.argv[i+1]

    ensure_directories()

    logger.info(f"Loading data from {data_path}")
    try:
        df = load_cleaned_data(data_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info("Preparing model data")
    X, y, feature_names = prepare_model_data(df)

    # Parameters
    alpha_grid = [0.1, 1.0, 10.0]
    cv_folds = 5
    seed = 42
    n_permutations = PERMUTATION_COUNT

    logger.info("Running Ridge Regression with Nested CV")
    model_results = run_ridge_regression_with_nested_cv(X, y, alpha_grid, cv_folds, seed)

    # Save residuals
    residuals_path = "data/processed/residuals.csv"
    residuals_df = pd.DataFrame({
        "Subject_ID": df["Subject_ID"].values,
        "residual_raw": model_results["residuals"],
        "residual_standardized": (np.array(model_results["residuals"]) - np.mean(model_results["residuals"])) / np.std(model_results["residuals"])
    })
    residuals_df.to_csv(residuals_path, index=False)
    logger.info(f"Saved residuals to {residuals_path}")

    # Save full model results
    results_path = "data/results/full_model.json"
    write_json(results_path, {
        "mae": model_results["mae"],
        "r": model_results["r"],
        "r2": model_results["r2"],
        "alpha": model_results["alpha"]
    })
    logger.info(f"Saved full model results to {results_path}")

    # T021: Run Null Permutations
    logger.info(f"Running {n_permutations} permutation tests...")
    null_results = run_null_distribution_analysis(X, y, alpha_grid, cv_folds, n_permutations, seed)

    # T022: Calculate p-value (simplified here, logic depends on T022 task)
    observed_mae = model_results["mae"]
    null_maes = [r["mae"] for r in null_results]
    # Proportion of null MAEs <= observed MAE (assuming lower MAE is better, but usually we test if observed is better than null)
    # If null is random, observed should be lower (better).
    # p-value = count(null <= observed) / N  (if we are testing if observed is significantly better/low)
    # Or count(null >= observed) if we are testing if observed is worse.
    # Standard: p = (1 + sum(null <= observed)) / (1 + N) for two-tailed or specific direction.
    # Task T022 says: "proportion of null MAEs <= observed MAE"
    p_value = sum(1 for mae in null_maes if mae <= observed_mae) / len(null_maes)

    null_dist_path = "data/results/null_distribution.json"
    write_json(null_dist_path, {
        "permutations": null_results,
        "observed_mae": observed_mae,
        "p_value": p_value
    })
    logger.info(f"Saved null distribution to {null_dist_path}")

    # Plot
    plot_path = "data/results/null_dist.png"
    plot_null_distribution(null_results, observed_mae, plot_path)
    logger.info(f"Saved null distribution plot to {plot_path}")

    logger.info("Modeling pipeline completed successfully.")

if __name__ == "__main__":
    main()