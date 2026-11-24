import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

from utils import get_logger, setup_logging, read_json, write_json
from config import ensure_directories

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PERMUTATION_COUNT = 100
SEED = 42


def load_cleaned_data(data_path: str) -> pd.DataFrame:
    """Load the cleaned dataset produced by the ingestion step."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    return pd.read_csv(data_path)


def prepare_model_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Assemble feature matrix ``X`` and target vector ``y``.

    Expected columns:
        - Global_Signal_SD
        - Mean_FD
        - Mean_DVARS
        - Age
        - Sex (binary encoded if necessary)
        - MWQ_Score (target)
    """
    target = "MWQ_Score"
    features = ["Global_Signal_SD", "Mean_FD", "Mean_DVARS", "Age"]

    if "Sex" in df.columns:
        # Encode sex as 0/1 if it is categorical
        if df["Sex"].dtype == object:
            df["Sex"] = df["Sex"].map({"M": 0, "F": 1}).fillna(0)
        features.append("Sex")

    missing = [c for c in features if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")
    if target not in df.columns:
        raise ValueError(f"Missing target column: {target}")

    X = df[features].values
    y = df[target].values
    return X, y, features


def run_ridge_regression_with_nested_cv(
    X: np.ndarray,
    y: np.ndarray,
    alpha_grid: List[float],
    cv_folds: int,
    seed: int,
) -> Dict[str, Any]:
    """
    Perform nested cross‑validation for ridge regression.

    * Outer CV (``cv_folds``) estimates out‑of‑fold performance.
    * Inner CV (3‑fold) selects the best ``alpha`` from ``alpha_grid``.

    Returns a dictionary with MAE, Pearson r, R², the average selected alpha,
    and the residuals for each outer‑fold test observation.
    """
    rng = np.random.RandomState(seed)
    outer_cv = KFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    inner_cv = KFold(n_splits=3, shuffle=True, random_state=seed)

    mae_list = []
    r_list = []
    r2_list = []
    alphas = []
    residuals = []
    y_true_all = []
    y_pred_all = []

    scaler = StandardScaler()

    for train_idx, test_idx in outer_cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Standardise features based on training data
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Inner CV to pick the best alpha
        ridge_cv = RidgeCV(alphas=alpha_grid, cv=inner_cv, store_cv_values=True)
        ridge_cv.fit(X_train_scaled, y_train)

        best_alpha = ridge_cv.alpha_
        alphas.append(best_alpha)

        # Predict on the outer test set
        y_pred = ridge_cv.predict(X_test_scaled)

        mae = np.mean(np.abs(y_test - y_pred))
        mae_list.append(mae)

        # Pearson correlation
        r = np.corrcoef(y_test, y_pred)[0, 1]
        r_list.append(r)

        # R²
        ss_res = np.sum((y_test - y_pred) ** 2)
        ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
        r2 = 1 - ss_res / ss_tot
        r2_list.append(r2)

        # Store residuals and true/predicted values for later aggregation
        residuals.extend(y_test - y_pred)
        y_true_all.extend(y_test)
        y_pred_all.extend(y_pred)

    results = {
        "mae": float(np.mean(mae_list)),
        "r": float(np.mean(r_list)),
        "r2": float(np.mean(r2_list)),
        "alpha": float(np.mean(alphas)),
        "residuals": residuals,
        "actuals": y_true_all,
        "predictions": y_pred_all,
    }
    return results


def run_null_distribution_analysis(
    X: np.ndarray,
    y: np.ndarray,
    alpha_grid: List[float],
    cv_folds: int,
    n_permutations: int,
    seed: int,
) -> List[Dict[str, float]]:
    """
    Generate a null distribution by permuting the outcome vector ``y``.

    The function enforces that exactly ``n_permutations`` iterations are
    completed (Task T045). If any iteration fails, a ``RuntimeError`` is
    raised.
    """
    rng = np.random.RandomState(seed)
    results = []
    completed = 0

    for i in range(n_permutations):
        y_perm = y.copy()
        rng.shuffle(y_perm)

        try:
            perm_res = run_ridge_regression_with_nested_cv(
                X, y_perm, alpha_grid, cv_folds, seed + i
            )
            results.append({"mae": perm_res["mae"], "r2": perm_res["r2"]})
            completed += 1
        except Exception as exc:
            logging.error(f"Permutation {i} failed: {exc}")
            # Propagate the error – we cannot silently drop permutations.
            raise

    if completed != n_permutations:
        raise RuntimeError(
            f"Permutation count mismatch: expected {n_permutations}, got {completed}"
        )
    return results


def plot_null_distribution(null_results: List[Dict], observed_mae: float, output_path: str):
    """Create and save a histogram of the null MAE distribution."""
    null_maes = [r["mae"] for r in null_results]
    plt.figure(figsize=(8, 5))
    plt.hist(null_maes, bins=30, color="steelblue", edgecolor="black", alpha=0.7)
    plt.axvline(observed_mae, color="red", linestyle="--", label=f"Observed MAE = {observed_mae:.3f}")
    plt.xlabel("MAE (null distribution)")
    plt.ylabel("Frequency")
    plt.title("Null Distribution of MAE")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main():
    """
    Entry point for the modeling pipeline.

    The script:
    1. Loads ``cleaned_data.csv``.
    2. Runs ridge regression with nested CV.
    3. Writes residuals and model metrics.
    4. Generates a null distribution (100 permutations) and saves the plot.
    """
    logger = get_logger(__name__)
    setup_logging()

    # ------------------------------------------------------------------
    # Resolve data path (allow override via CLI)
    # ------------------------------------------------------------------
    data_path = "data/processed/cleaned_data.csv"
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--data" and i + 1 < len(sys.argv):
                data_path = sys.argv[i + 1]

    ensure_directories()

    logger.info(f"Loading cleaned data from {data_path}")
    try:
        df = load_cleaned_data(data_path)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        sys.exit(1)

    # ------------------------------------------------------------------
    # Prepare features / target
    # ------------------------------------------------------------------
    X, y, feature_names = prepare_model_data(df)

    # ------------------------------------------------------------------
    # Model fitting
    # ------------------------------------------------------------------
    alpha_grid = [0.1, 1.0, 10.0]
    cv_folds = 5
    logger.info("Running ridge regression with nested cross‑validation")
    model_res = run_ridge_regression_with_nested_cv(
        X, y, alpha_grid, cv_folds, SEED
    )

    # ------------------------------------------------------------------
    # Write residuals
    # ------------------------------------------------------------------
    residuals_path = "data/processed/residuals.csv"
    residuals_df = pd.DataFrame(
        {
            "Subject_ID": df["Subject_ID"],
            "residual_raw": model_res["residuals"],
        }
    )
    residuals_df.to_csv(residuals_path, index=False)
    logger.info(f"Residuals saved to {residuals_path}")

    # ------------------------------------------------------------------
    # Save primary model results
    # ------------------------------------------------------------------
    results_path = "data/results/full_model.json"
    write_json(
        results_path,
        {
            "mae": model_res["mae"],
            "r": model_res["r"],
            "r2": model_res["r2"],
            "alpha": model_res["alpha"],
        },
    )
    logger.info(f"Full model results written to {results_path}")

    # ------------------------------------------------------------------
    # Null‑distribution generation
    # ------------------------------------------------------------------
    logger.info(f"Running {PERMUTATION_COUNT} permutation tests for null distribution")
    null_res = run_null_distribution_analysis(
        X, y, alpha_grid, cv_folds, PERMUTATION_COUNT, SEED
    )

    # Compute empirical p‑value (proportion of null MAE <= observed MAE)
    observed_mae = model_res["mae"]
    p_value = sum(1 for r in null_res if r["mae"] <= observed_mae) / len(null_res)

    null_path = "data/results/null_distribution.json"
    write_json(
        null_path,
        {
            "permutations": null_res,
            "observed_mae": observed_mae,
            "p_value": p_value,
        },
    )
    logger.info(f"Null distribution saved to {null_path}")

    # ------------------------------------------------------------------
    # Plot null distribution
    # ------------------------------------------------------------------
    plot_path = "data/results/null_dist.png"
    plot_null_distribution(null_res, observed_mae, plot_path)
    logger.info(f"Null distribution plot saved to {plot_path}")

    logger.info("Modeling pipeline completed successfully.")


if __name__ == "__main__":
    main()
