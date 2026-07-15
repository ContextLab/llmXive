"""
Analysis module for computing correlations, VIF, training models,
and performing cross-validation.
"""

import os
import json
import logging
import csv
import pickle
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

# Constants
RESULTS_DIR = Path("results")
MODELS_DIR = Path("models")
DATA_PROCESSED_DIR = Path("data/processed")
METRICS_CSV_PATH = DATA_PROCESSED_DIR / "metrics.csv"
FILTERED_FEATURES_CSV_PATH = DATA_PROCESSED_DIR / "filtered_features.csv"
CORRELATIONS_JSON_PATH = RESULTS_DIR / "correlations.json"
MODEL_PERFORMANCE_JSON_PATH = RESULTS_DIR / "model_performance.json"
POWER_ANALYSIS_LOG_PATH = RESULTS_DIR / "power_analysis.log"
THERMAL_PREDICTOR_PATH = MODELS_DIR / "thermal_predictor.pkl"
VIF_THRESHOLD = 5.0
R2_THRESHOLD = 0.30


def setup_analysis_logger() -> logging.Logger:
    """Set up and return the analysis logger."""
    logger = logging.getLogger("analysis")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def load_metrics_csv() -> pd.DataFrame:
    """Load the metrics CSV file."""
    if not METRICS_CSV_PATH.exists():
        raise FileNotFoundError(f"Metrics file not found: {METRICS_CSV_PATH}")
    return pd.read_csv(METRICS_CSV_PATH)


def get_network_metrics(df: pd.DataFrame) -> List[str]:
    """Return list of network metric columns."""
    metric_cols = [
        "avg_degree",
        "avg_shortest_path_length",
        "clustering_coefficient",
        "density"
    ]
    return [col for col in metric_cols if col in df.columns]


def get_thermal_conductivity_col(df: pd.DataFrame) -> Optional[str]:
    """Return the thermal conductivity column name."""
    thermal_cols = [col for col in df.columns if "thermal_conductivity" in col.lower()]
    if not thermal_cols:
        return None
    return thermal_cols[0]


def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """Calculate VIF for each feature."""
    vif_data = {}
    for feature in features:
        try:
            vif = variance_inflation_factor(df[features].values, features.index(feature))
            vif_data[feature] = vif
        except Exception as e:
            vif_data[feature] = float('nan')
    return vif_data


def log_vif_results(vif_data: Dict[str, float], logger: logging.Logger) -> None:
    """Log VIF results to power_analysis.log."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(POWER_ANALYSIS_LOG_PATH, "a") as f:
        f.write("\n--- VIF Analysis ---\n")
        for feature, vif in vif_data.items():
            status = "INCLUDED" if vif < VIF_THRESHOLD else "EXCLUDED"
            f.write(f"{feature}: VIF={vif:.4f} [{status}]\n")


def generate_filtered_features_csv(df: pd.DataFrame, features: List[str], vif_data: Dict[str, float], logger: logging.Logger) -> pd.DataFrame:
    """Generate filtered_features.csv with only features having VIF < threshold."""
    filtered_features = [f for f in features if vif_data.get(f, float('nan')) < VIF_THRESHOLD]
    logger.info(f"Filtered features: {filtered_features}")
    
    # Log excluded features
    excluded = [f for f in features if f not in filtered_features]
    for f in excluded:
        logger.warning(f"Excluded feature '{f}' (VIF={vif_data.get(f, float('nan')):.4f} >= {VIF_THRESHOLD})")
    
    # Create filtered dataframe
    thermal_col = get_thermal_conductivity_col(df)
    if thermal_col:
        filtered_df = df[filtered_features + [thermal_col]].copy()
    else:
        filtered_df = df[filtered_features].copy()
    
    filtered_df.to_csv(FILTERED_FEATURES_CSV_PATH, index=False)
    logger.info(f"Saved filtered features to {FILTERED_FEATURES_CSV_PATH}")
    return filtered_df


def train_linear_model(X: np.ndarray, y: np.ndarray, logger: logging.Logger) -> LinearRegression:
    """Train a linear regression model."""
    model = LinearRegression()
    model.fit(X, y)
    logger.info("Linear regression model trained.")
    return model


def run_stratified_cross_validation(
    df: pd.DataFrame, 
    features: List[str], 
    thermal_col: str, 
    logger: logging.Logger
) -> Tuple[List[float], List[float], Dict[str, Any]]:
    """
    Perform 5-fold stratified cross-validation.
    Bins thermal conductivity into 5 quantile strata.
    Returns R² scores, RMSE scores, and interpretation.
    """
    y = df[thermal_col].values
    X = df[features].values

    # Handle NaNs in X or y
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X_clean = X[mask]
    y_clean = y[mask]

    if len(y_clean) < 5:
        logger.warning("Insufficient data for cross-validation.")
        return [], [], {"r2_interpretation": "Insufficient data."}

    # Bin thermal conductivity into 5 quantile strata
    try:
        strata = pd.qcut(y_clean, q=5, labels=False, duplicates='drop')
    except ValueError:
        # Fallback to uniform bins if qcut fails
        strata = pd.cut(y_clean, bins=5, labels=False)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    r2_scores = []
    rmse_scores = []

    for train_idx, test_idx in skf.split(X_clean, strata):
        X_train, X_test = X_clean[train_idx], X_clean[test_idx]
        y_train, y_test = y_clean[train_idx], y_clean[test_idx]

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = LinearRegression()
        model.fit(X_train_scaled, y_train)

        y_pred = model.predict(X_test_scaled)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))

        r2_scores.append(r2)
        rmse_scores.append(rmse)

    mean_r2 = np.mean(r2_scores)
    std_r2 = np.std(r2_scores)
    mean_rmse = np.mean(rmse_scores)
    std_rmse = np.std(rmse_scores)

    interpretation = ""
    if mean_r2 < R2_THRESHOLD:
        interpretation = "Weak predictive power (R² < 0.30), consistent with null hypothesis."
        logger.warning(interpretation)

    cv_results = {
        "r2_scores": r2_scores,
        "rmse_scores": rmse_scores,
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "mean_rmse": mean_rmse,
        "std_rmse": std_rmse,
        "r2_interpretation": interpretation if interpretation else None
    }

    return r2_scores, rmse_scores, cv_results


def main() -> None:
    """Main entry point for analysis."""
    logger = setup_analysis_logger()
    logger.info("Starting analysis...")

    # Load metrics
    df = load_metrics_csv()
    logger.info(f"Loaded {len(df)} records from {METRICS_CSV_PATH}")

    # Get columns
    network_metrics = get_network_metrics(df)
    thermal_col = get_thermal_conductivity_col(df)

    if not thermal_col:
        logger.error("Thermal conductivity column not found.")
        raise ValueError("Thermal conductivity column not found in metrics.csv")

    # 1. Compute Correlations
    logger.info("Computing correlations...")
    correlations = {}
    for metric in network_metrics:
        if metric in df.columns:
            pearson_r, pearson_p = stats.pearsonr(df[metric], df[thermal_col])
            spearman_r, spearman_p = stats.spearmanr(df[metric], df[thermal_col])
            correlations[metric] = {
                "pearson": {"r": pearson_r, "p": pearson_p},
                "spearman": {"r": spearman_r, "p": spearman_p}
            }

    # Bonferroni correction
    n_tests = len(network_metrics)
    alpha = 0.05
    corrected_alpha = alpha / n_tests
    logger.info(f"Bonferroni-corrected alpha: {corrected_alpha}")

    correlations["bonferroni"] = {
        "alpha": alpha,
        "n_tests": n_tests,
        "corrected_alpha": corrected_alpha
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CORRELATIONS_JSON_PATH, "w") as f:
        json.dump(correlations, f, indent=2)
    logger.info(f"Saved correlations to {CORRELATIONS_JSON_PATH}")

    # 2. VIF Calculation and Filtering
    logger.info("Calculating VIF...")
    vif_data = calculate_vif(df, network_metrics)
    log_vif_results(vif_data, logger)
    
    filtered_df = generate_filtered_features_csv(df, network_metrics, vif_data, logger)
    filtered_features = [f for f in network_metrics if vif_data.get(f, float('nan')) < VIF_THRESHOLD]

    if not filtered_features:
        logger.warning("No features passed VIF filter. Cannot train model.")
        return

    # 3. Train Model
    logger.info("Training linear regression model...")
    X = filtered_df[filtered_features].values
    y = filtered_df[thermal_col].values

    # Handle NaNs
      # Remove rows with NaNs
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X_clean = X[mask]
    y_clean = y[mask]

    if len(y_clean) == 0:
        logger.error("No valid data after NaN removal.")
        return

    model = train_linear_model(X_clean, y_clean, logger)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(THERMAL_PREDICTOR_PATH, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {THERMAL_PREDICTOR_PATH}")

    # 4. Cross-Validation
    logger.info("Running stratified cross-validation...")
    r2_scores, rmse_scores, cv_results = run_stratified_cross_validation(
        filtered_df, filtered_features, thermal_col, logger
    )

    # Save model performance
    performance = {
        "r2_scores": cv_results["r2_scores"],
        "rmse_scores": cv_results["rmse_scores"],
        "mean_r2": cv_results["mean_r2"],
        "std_r2": cv_results["std_r2"],
        "mean_rmse": cv_results["mean_rmse"],
        "std_rmse": cv_results["std_rmse"]
    }
    
    if cv_results.get("r2_interpretation"):
        performance["r2_interpretation"] = cv_results["r2_interpretation"]

    with open(MODEL_PERFORMANCE_JSON_PATH, "w") as f:
        json.dump(performance, f, indent=2)
    logger.info(f"Saved model performance to {MODEL_PERFORMANCE_JSON_PATH}")

    logger.info("Analysis complete.")


if __name__ == "__main__":
    main()
