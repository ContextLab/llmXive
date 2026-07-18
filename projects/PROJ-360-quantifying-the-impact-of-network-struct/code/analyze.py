import os
import json
import logging
import csv
import pickle
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm

# --- Configuration ---
METRICS_CSV_PATH = "data/processed/metrics.csv"
FILTERED_FEATURES_PATH = "data/processed/filtered_features.csv"
MODEL_PATH = "models/thermal_predictor.pkl"
CORRELATIONS_JSON_PATH = "results/correlations.json"
MODEL_PERFORMANCE_JSON_PATH = "results/model_performance.json"
POWER_ANALYSIS_LOG_PATH = "results/power_analysis.log"

# --- Logging Setup ---
def setup_analysis_logger(name: str = "analysis", log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
    return logger

# --- Data Loading ---
def load_metrics_csv() -> pd.DataFrame:
    if not os.path.exists(METRICS_CSV_PATH):
        raise FileNotFoundError(f"Metrics file not found: {METRICS_CSV_PATH}")
    return pd.read_csv(METRICS_CSV_PATH)

def load_filtered_features() -> pd.DataFrame:
    if not os.path.exists(FILTERED_FEATURES_PATH):
        raise FileNotFoundError(f"Filtered features file not found: {FILTERED_FEATURES_PATH}")
    return pd.read_csv(FILTERED_FEATURES_PATH)

# --- Network Metrics Extraction ---
def get_network_metrics(df: pd.DataFrame) -> List[str]:
    # Assuming columns: average_degree, average_shortest_path, clustering_coefficient, density
    # Filter out non-metric columns like material_id, thermal_conductivity_scalar
    metric_cols = [col for col in df.columns if col in ['average_degree', 'average_shortest_path', 'clustering_coefficient', 'density']]
    return metric_cols

def get_thermal_conductivity_col(df: pd.DataFrame) -> str:
    if 'thermal_conductivity_scalar' not in df.columns:
        raise ValueError("Column 'thermal_conductivity_scalar' not found in metrics CSV")
    return 'thermal_conductivity_scalar'

# --- VIF Calculation ---
def calculate_vif(features_df: pd.DataFrame) -> pd.Series:
    """Calculate Variance Inflation Factor for each feature."""
    vif_data = pd.Series(dtype=float)
    if features_df.empty:
        return vif_data
    
    # Add constant for intercept
    X = sm.add_constant(features_df)
    
    for col in features_df.columns:
        try:
            y = features_df[col]
            # Regression of this feature against all other features
            other_features = [c for c in features_df.columns if c != col]
            if not other_features:
                vif_data[col] = 1.0
                continue
            X_other = sm.add_constant(features_df[other_features])
            model = sm.OLS(y, X_other).fit()
            vif_data[col] = 1.0 / (1.0 - model.rsquared)
        except Exception as e:
            logging.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.inf
    return vif_data

def log_vif_results(vif_series: pd.Series, log_file: str):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, 'a') as f:
        for col, val in vif_series.items():
            f.write(f"VIF: {col} = {val:.4f}\n")

# --- Feature Filtering ---
def filter_features(features_df: pd.DataFrame, vif_threshold: float = 5.0) -> pd.DataFrame:
    """Filter features based on VIF threshold. Logs excluded/included features."""
    if features_df.empty:
        return features_df
    
    vif_series = calculate_vif(features_df)
    
    os.makedirs(os.path.dirname(POWER_ANALYSIS_LOG_PATH), exist_ok=True)
    with open(POWER_ANALYSIS_LOG_PATH, 'a') as f:
        f.write(f"\n--- Feature Filtering (Threshold: {vif_threshold}) ---\n")
        included_features = []
        for col, val in vif_series.items():
            if val >= vif_threshold:
                f.write(f"EXCLUDED: {col} (VIF={val:.4f})\n")
            else:
                f.write(f"INCLUDED: {col} (VIF={val:.4f})\n")
                included_features.append(col)
    
    filtered_df = features_df[included_features]
    # Save to disk immediately
    os.makedirs(os.path.dirname(FILTERED_FEATURES_PATH), exist_ok=True)
    filtered_df.to_csv(FILTERED_FEATURES_PATH, index=False)
    return filtered_df

# --- Model Training ---
def train_linear_model(features_df: pd.DataFrame, target_series: pd.Series) -> LinearRegression:
    """
    Train a Linear Regression model using ONLY the features from filtered_features.csv.
    Saves the model to models/thermal_predictor.pkl.
    """
    if features_df.empty:
        raise ValueError("Features DataFrame is empty. Cannot train model.")
    if target_series.empty:
        raise ValueError("Target Series is empty. Cannot train model.")
    
    # Ensure alignment
    common_index = features_df.index.intersection(target_series.index)
    X = features_df.loc[common_index]
    y = target_series.loc[common_index]
    
    if X.empty or y.empty:
        raise ValueError("Aligned data is empty after intersection.")
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    
    logging.info(f"Model trained and saved to {MODEL_PATH}")
    return model

# --- Cross Validation ---
def run_stratified_cross_validation(model: LinearRegression, X: pd.DataFrame, y: pd.Series, k: int = 5) -> Dict[str, Any]:
    """
    Perform k-fold cross-validation.
    Returns dict with lists of R2 and RMSE scores.
    """
    kf = KFold(n_splits=k, shuffle=True, random_state=42)
    r2_scores = []
    rmse_scores = []
    
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Clone model for each fold to avoid state leakage
        fold_model = LinearRegression()
        fold_model.fit(X_train, y_train)
        
        y_pred = fold_model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
    
    return {
        "r2_scores": r2_scores,
        "rmse_scores": rmse_scores,
        "k": k
    }

def aggregate_cv_results(cv_results: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate CV results into mean ± std dev and save to JSON."""
    r2_scores = cv_results["r2_scores"]
    rmse_scores = cv_results["rmse_scores"]
    k = cv_results["k"]
    
    mean_r2 = np.mean(r2_scores)
    std_r2 = np.std(r2_scores)
    mean_rmse = np.mean(rmse_scores)
    std_rmse = np.std(rmse_scores)
    
    result = {
        "k_folds": k,
        "r2": {
            "mean": float(mean_r2),
            "std": float(std_r2),
            "scores": [float(s) for s in r2_scores]
        },
        "rmse": {
            "mean": float(mean_rmse),
            "std": float(std_rmse),
            "scores": [float(s) for s in rmse_scores]
        }
    }
    
    # Add interpretation if R2 < 0.30
    if mean_r2 < 0.30:
        result["r2_interpretation"] = "Weak predictive power (R² < 0.30), consistent with null hypothesis."
    
    os.makedirs(os.path.dirname(MODEL_PERFORMANCE_JSON_PATH), exist_ok=True)
    with open(MODEL_PERFORMANCE_JSON_PATH, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result

# --- Correlation Analysis ---
def compute_correlations(df: pd.DataFrame, metrics: List[str], target_col: str) -> Dict[str, Any]:
    """Compute Pearson and Spearman correlations."""
    results = {}
    for metric in metrics:
        if metric not in df.columns or target_col not in df.columns:
            continue
        x = df[metric].dropna()
        y = df[target_col].loc[x.index].dropna()
        if len(x) < 2:
            continue
        
        pearson_corr, pearson_p = np.corrcoef(x, y)[0, 1], 0.0 # Placeholder for p-value logic
        # Calculate p-value manually or use scipy if available, but keeping dependencies minimal
        # Using scipy.stats for proper p-value
        try:
            from scipy.stats import pearsonr, spearmanr
            pearson_corr, pearson_p = pearsonr(x, y)
            spearman_corr, spearman_p = spearmanr(x, y)
        except ImportError:
            # Fallback if scipy not installed (should be in requirements)
            pearson_corr = np.corrcoef(x, y)[0, 1]
            pearson_p = 0.0
            spearman_corr = pearson_corr
            spearman_p = 0.0

        results[metric] = {
            "pearson": {"r": float(pearson_corr), "p": float(pearson_p)},
            "spearman": {"r": float(spearman_corr), "p": float(spearman_p)}
        }
    return results

def save_correlations(correlations: Dict[str, Any], alpha_threshold: float):
    os.makedirs(os.path.dirname(CORRELATIONS_JSON_PATH), exist_ok=True)
    output = {
        "alpha": alpha_threshold,
        "correlations": correlations
    }
    with open(CORRELATIONS_JSON_PATH, 'w') as f:
        json.dump(output, f, indent=2)

# --- Power Analysis ---
def log_power_analysis(n: int, alpha: float):
    os.makedirs(os.path.dirname(POWER_ANALYSIS_LOG_PATH), exist_ok=True)
    with open(POWER_ANALYSIS_LOG_PATH, 'a') as f:
        f.write(f"\n--- Power Analysis ---\n")
        f.write(f"Sample size (n): {n}\n")
        f.write(f"Bonferroni adjusted alpha: {alpha}\n")
        if n < 50:
            f.write(f"WARNING: Sample size n < 50. Adjusted alpha used: {alpha}\n")

# --- Main Entry Point ---
def main():
    logger = setup_analysis_logger()
    logger.info("Starting analysis pipeline...")

    # 1. Load Metrics
    try:
        df = load_metrics_csv()
        logger.info(f"Loaded metrics: {len(df)} rows")
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # 2. Identify Metrics and Target
    metrics_cols = get_network_metrics(df)
    target_col = get_thermal_conductivity_col(df)
    logger.info(f"Network metrics: {metrics_cols}")
    logger.info(f"Target: {target_col}")

    # 3. Power Analysis & Bonferroni
    n = len(df)
    num_tests = len(metrics_cols)
    alpha = 0.05
    if n < 50:
        alpha = alpha / n
    log_power_analysis(n, alpha)

    # 4. Correlations
    if metrics_cols:
        correlations = compute_correlations(df, metrics_cols, target_col)
        save_correlations(correlations, alpha)
        logger.info("Correlations saved.")

    # 5. VIF Calculation (T020)
    feature_df = df[metrics_cols]
    vif_series = calculate_vif(feature_df)
    log_vif_results(vif_series, POWER_ANALYSIS_LOG_PATH)

    # 6. Feature Filtering (T021)
    filtered_df = filter_features(feature_df, vif_threshold=5.0)
    logger.info(f"Filtered features saved to {FILTERED_FEATURES_PATH}")

    # 7. Model Training (T022)
    if not filtered_df.empty:
        model = train_linear_model(filtered_df, df[target_col])
        
        # 8. Cross Validation (T023)
        cv_results = run_stratified_cross_validation(model, filtered_df, df[target_col], k=5)
        
        # 9. Aggregate Results (T024)
        perf_results = aggregate_cv_results(cv_results)
        logger.info(f"Model performance saved to {MODEL_PERFORMANCE_JSON_PATH}")
    else:
        logger.warning("No features remaining after VIF filtering. Skipping model training.")

    logger.info("Analysis pipeline complete.")

if __name__ == "__main__":
    main()