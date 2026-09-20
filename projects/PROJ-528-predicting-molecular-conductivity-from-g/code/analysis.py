import os
import json
import logging
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.inspection import permutation_importance
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
from code.config import SEED, VIF_THRESHOLD, OUTLIER_SIGMA
from code.scaffold_split import scaffold_split

logger = logging.getLogger(__name__)

def filter_outliers(df: pd.DataFrame, target_col: str, sigma_threshold: float) -> pd.DataFrame:
    """Filter rows where |z_score| <= sigma_threshold for target_col."""
    mean_val = df[target_col].mean()
    std_val = df[target_col].std()
    if std_val == 0:
        logger.warning("Standard deviation is zero, no outliers to filter.")
        return df
    z_scores = (df[target_col] - mean_val) / std_val
    filtered_df = df[abs(z_scores) <= sigma_threshold].copy()
    logger.info(f"Filtered outliers: kept {len(filtered_df)} rows (threshold={sigma_threshold})")
    return filtered_df

def calculate_vif(X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
    """Calculate VIF for each feature."""
    vif_data = {}
    for i, name in enumerate(feature_names):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data[name] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {name}: {e}")
            vif_data[name] = float('inf')
    return vif_data

def exclude_high_vif_features(vif_scores: Dict[str, float], threshold: float) -> List[str]:
    """Return list of features with VIF > threshold."""
    return [k for k, v in vif_scores.items() if v > threshold]

def train_and_evaluate_model(X: np.ndarray, y: pd.Series, seed: int) -> Tuple[Any, Any, float, float, float, float]:
    """Train RF and GB, return models and metrics."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=seed)

    rf = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed)
    gb = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, random_state=seed)

    rf.fit(X_train, y_train)
    gb.fit(X_train, y_train)

    r2_rf = r2_score(y_test, rf.predict(X_test))
    r2_gb = r2_score(y_test, gb.predict(X_test))
    mae_rf = mean_absolute_error(y_test, rf.predict(X_test))
    mae_gb = mean_absolute_error(y_test, gb.predict(X_test))

    return rf, gb, r2_rf, r2_gb, mae_rf, mae_gb

def run_vif_iterative_loop(
    X: np.ndarray,
    y: pd.Series,
    target_name: str,
    vif_threshold: float,
    seed: int
) -> Tuple[Dict, np.ndarray, List[str], float, float]:
    """
    Iteratively remove features with VIF > threshold and retrain.
    Returns: vif_log, final_X, final_features, final_r2, final_mae
    """
    feature_names = list(range(X.shape[1])) # Using indices if names not passed, but we need names for log
    # Actually, we need names. Let's assume X columns are ordered and we pass names separately or infer.
    # For this function, we assume X is a DataFrame or we track names.
    # Re-implementing to accept feature_names list if X is numpy, but easier if X is DataFrame.
    # Let's assume X is numpy and we have a parallel list of names.
    # But the function signature above takes X as np.ndarray.
    # We will assume the caller passes X as DataFrame or we handle names inside.
    # To be safe, let's assume X is DataFrame in this context or we pass names.
    # Let's change signature slightly to accept feature_names.
    pass

def run_vif_iterative_loop(
    X: pd.DataFrame,
    y: pd.Series,
    target_name: str,
    vif_threshold: float,
    seed: int
) -> Tuple[Dict, pd.DataFrame, List[str], float, float]:
    """
    Iteratively remove features with VIF > threshold and retrain.
    Returns: vif_log, final_X, final_features, final_r2, final_mae
    """
    iterations = []
    current_X = X.copy()
    current_features = list(current_X.columns)
    final_r2 = 0.0
    final_mae = 0.0
    iteration_count = 0

    while True:
        iteration_count += 1
        logger.info(f"VIF Iteration {iteration_count}: {len(current_features)} features")

        if len(current_features) == 0:
            logger.critical("All features excluded. Stopping.")
            break

        # Calculate VIF
        vif_scores = calculate_vif(current_X.values, current_features)
        high_vif = exclude_high_vif_features(vif_scores, vif_threshold)

        if not high_vif:
            logger.info("No features with VIF > threshold. Stopping loop.")
            break

        # Exclude the feature with the HIGHEST VIF
        max_vif_feature = max(vif_scores, key=vif_scores.get)
        logger.info(f"Excluding feature with highest VIF: {max_vif_feature} (VIF={vif_scores[max_vif_feature]:.2f})")

        # Record iteration
        iterations.append({
            "iteration": iteration_count,
            "excluded_feature": max_vif_feature,
            "vif_scores": vif_scores,
            "remaining_features": [f for f in current_features if f != max_vif_feature]
        })

        # Remove feature
        current_X = current_X.drop(columns=[max_vif_feature])
        current_features = list(current_X.columns)

        # Retrain and evaluate
        rf, gb, r2_rf, r2_gb, mae_rf, mae_gb = train_and_evaluate_model(
            current_X.values, y, seed
        )
        # Store best model metrics (e.g., GB)
        final_r2 = r2_gb
        final_mae = mae_gb

        iterations[-1]["r2"] = final_r2
        iterations[-1]["mae"] = final_mae

    vif_log = {"iterations": iterations}
    return vif_log, current_X, current_features, final_r2, final_mae

def update_model_results(results_path: str, new_metrics: Dict[str, Any]) -> None:
    """Update model_results.json with new metrics."""
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    data.update(new_metrics)
    with open(results_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Updated model results at {results_path}")

def calculate_feature_correlations(df: pd.DataFrame, target_col: str) -> Dict[str, Tuple[float, float]]:
    """Calculate Pearson correlation and p-value for each feature vs target."""
    correlations = {}
    for col in df.columns:
        if col == target_col:
            continue
        corr, pval = stats.pearsonr(df[col], df[target_col])
        correlations[col] = (float(corr), float(pval))
    return correlations

def apply_bh_correction(p_values: List[float]) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    if not p_values:
        return []
    _, corrected, _, _ = multipletests(p_values, method='fdr_bh')
    return corrected.tolist()

def main():
    parser = argparse.ArgumentParser(description="Run analysis (T039, T040, etc.)")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv")
    parser.add_argument("--results", type=str, default="data/processed/model_results.json")
    parser.add_argument("--plots", type=str, default="data/processed/correlation_plots/")
    args = parser.parse_args()

    setup_logging()
    logger.info("Starting Analysis")

    # Placeholder for main logic if called directly
    logger.info("Analysis module loaded.")

if __name__ == "__main__":
    main()
