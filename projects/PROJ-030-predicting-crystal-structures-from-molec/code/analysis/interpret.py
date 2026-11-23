import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from joblib import load as joblib_load

# Import project utilities
from config import get_path_results, get_path_models, get_path_processed_data, ensure_directory
from logging_config import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_model(model_path: str):
    """Load a model from a pickle or joblib file."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    # Try joblib first (common for sklearn), then pickle
    try:
        return joblib_load(model_path)
    except Exception:
        import pickle
        with open(model_path, 'rb') as f:
            return pickle.load(f)

def load_dataset_features_and_targets(dataset_path: str, target_col: str, feature_prefix: str = "fp_") -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load dataset, extract features (fingerprint bits) and target.
    Returns (X, y, feature_names).
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    
    # Identify feature columns (assuming they start with 'fp_' or similar based on fingerprint task)
    # If columns are just 0, 1, 2... or specific bit names, adjust logic.
    # Based on T011/T012, fingerprints are likely stored as comma-separated strings or expanded columns.
    # Assuming expanded columns for model training efficiency.
    
    # Heuristic: if 'fp_' prefix exists, use it. Otherwise, assume all numeric columns except target are features.
    feature_cols = [c for c in df.columns if c.startswith(feature_prefix)]
    
    if not feature_cols:
        # Fallback: assume all numeric columns except the target are features
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [c for c in numeric_cols if c != target_col]
    
    if len(feature_cols) == 0:
        raise ValueError(f"No feature columns found in {dataset_path}. Expected columns starting with '{feature_prefix}'.")
    
    X = df[feature_cols].values.astype(np.float32)
    y = df[target_col].values
    
    return X, y, feature_cols

def compute_shap_rf(X: np.ndarray, model: Any, feature_names: List[str], nsamples: int = 100) -> Dict[str, Any]:
    """
    Compute SHAP values for a Random Forest model.
    Returns a dictionary with summary data and top features.
    """
    logger.info("Initializing SHAP explainer for Random Forest...")
    explainer = shap.TreeExplainer(model)
    
    logger.info("Computing SHAP values (this may take a while)...")
    shap_values = explainer.shap_values(X)
    
    # Handle case where shap_values might be a list (for multi-class) or single array
    if isinstance(shap_values, list):
        # Multi-class: take the mean of absolute values across classes for ranking
        shap_abs = np.mean([np.abs(sv) for sv in shap_values], axis=0)
    else:
        shap_abs = np.abs(shap_values)
    
    # Aggregate importance
    mean_abs_shap = np.mean(shap_abs, axis=0)
    std_abs_shap = np.std(shap_abs, axis=0)
    
    # Sort by mean absolute SHAP value
    indices = np.argsort(mean_abs_shap)[::-1]
    
    top_k = 50
    top_indices = indices[:top_k]
    
    result = {
        "model_type": "RandomForest",
        "n_samples": X.shape[0],
        "n_features": X.shape[1],
        "top_features": [
            {
                "feature_name": feature_names[i],
                "mean_abs_shap": float(mean_abs_shap[i]),
                "std_abs_shap": float(std_abs_shap[i])
            }
            for i in top_indices
        ],
        "all_shap_stats": {
            "mean_abs_shap": mean_abs_shap.tolist(),
            "std_abs_shap": std_abs_shap.tolist()
        }
    }
    
    return result

def compute_shap_ridge(X: np.ndarray, y: np.ndarray, model: Any, feature_names: List[str]) -> Dict[str, Any]:
    """
    Compute SHAP values for a Ridge Regression model.
    For linear models, SHAP values are essentially the coefficient * (feature - expected_feature).
    We use KernelExplainer for generality or direct calculation for efficiency.
    """
    logger.info("Computing SHAP values for Ridge Regression...")
    
    # For linear models, SHAP values can be approximated as:
    # shap_value_i = coef_i * (x_i - mean_x_i)
    # But to be consistent with SHAP library and handle intercepts correctly:
    # We can use a simple linear explainer or KernelExplainer with a background sample.
    # Given the speed of Ridge, we use a small background sample for KernelExplainer.
    
    background = shap.kmeans(X, 10)  # 10 clusters for background
    explainer = shap.KernelExplainer(model.predict, background)
    
    # Compute SHAP values for a subset if X is huge to save memory/time, or all if manageable
    # Limit to first 1000 samples for the explanation calculation if dataset is large, 
    # but the importance ranking is derived from the coefficients which are global.
    # However, the task asks for SHAP values to identify top bits.
    # For linear models, the ranking is exactly the ranking of |coef|.
    # We will compute the full ranking via coefficients and sample SHAP values for the report.
    
    coef = model.coef_
    intercept = model.intercept_
    
    # Global importance based on coefficients
    abs_coef = np.abs(coef)
    indices = np.argsort(abs_coef)[::-1]
    
    top_k = 50
    top_indices = indices[:top_k]
    
    # For the report, we can compute SHAP values for a sample to show distribution
    sample_size = min(100, X.shape[0])
    sample_indices = np.random.choice(X.shape[0], sample_size, replace=False)
    X_sample = X[sample_indices]
    
    shap_values = explainer.shap_values(X_sample)
    
    result = {
        "model_type": "RidgeRegression",
        "n_samples": X.shape[0],
        "n_features": X.shape[1],
        "coefficients": {
            "mean_abs_coef": float(np.mean(np.abs(coef))),
            "max_abs_coef": float(np.max(np.abs(coef)))
        },
        "top_features": [
            {
                "feature_name": feature_names[i],
                "coef": float(coef[i]),
                "abs_coef": float(abs_coef[i])
            }
            for i in top_indices
        ],
        "sample_shap_stats": {
            "sample_size": sample_size,
            "mean_shap": np.mean(shap_values, axis=0).tolist(),
            "std_shap": np.std(shap_values, axis=0).tolist()
        }
    }
    
    return result

def main():
    """
    Main entry point for T023: Compute and save SHAP values.
    Targets:
      1. Random Forest (Space Group) -> data/results/shap_analysis_rf.json
      2. Ridge Regression (Lattice Parameters) -> data/results/shap_analysis_ridge.json
    Unified output: data/results/shap_analysis.json
    """
    logger.info("Starting T023: SHAP Analysis for Predictive Gap Analysis")
    
    # Paths
    dataset_path = get_path_processed_data("crystal_dataset.csv")
    rf_model_path = get_path_models("rf_model.pkl")
    ridge_model_path = get_path_models("ridge_model.pkl")
    output_path = get_path_results("shap_analysis.json")
    
    ensure_directory(output_path)
    
    results = {}
    
    # 1. Random Forest (Space Group)
    try:
        logger.info("Loading Random Forest model and dataset for Space Group prediction...")
        rf_model = load_model(rf_model_path)
        X_rf, y_rf, feature_names = load_dataset_features_and_targets(dataset_path, target_col="space_group_id")
        
        logger.info(f"Dataset shape: {X_rf.shape}, Features: {len(feature_names)}")
        
        shap_rf_result = compute_shap_rf(X_rf, rf_model, feature_names)
        results["random_forest_space_group"] = shap_rf_result
        logger.info("Completed SHAP analysis for Random Forest (Space Group).")
        
    except Exception as e:
        logger.error(f"Failed to compute SHAP for Random Forest: {e}", exc_info=True)
        results["random_forest_space_group"] = {"error": str(e)}
    
    # 2. Ridge Regression (Lattice Parameters)
    # Note: Lattice parameters might be multiple columns (a, b, c, alpha, beta, gamma) or a single composite target.
    # Based on T017/T019, the regression target is likely "lattice_params" or similar.
    # If it's a multi-output regression, we need to handle it. Assuming single target column "lattice_params" or similar.
    # Let's assume the target column name is "lattice_params" or "lattice_param_a" (first one).
    # We will try common names.
    target_candidates = ["lattice_params", "lattice_param_a", "lattice_a", "target_lattice"]
    target_col_ridge = None
    
    for candidate in target_candidates:
        try:
            # Quick check if column exists
            test_df = pd.read_csv(dataset_path)
            if candidate in test_df.columns:
                target_col_ridge = candidate
                break
        except Exception:
            continue
    
    if not target_col_ridge:
        # Fallback: try to find any column that looks like a lattice parameter
        test_df = pd.read_csv(dataset_path)
        cols = [c for c in test_df.columns if "lattice" in c.lower() or "param" in c.lower()]
        if cols:
            target_col_ridge = cols[0]
        else:
            raise ValueError("Could not identify lattice parameter target column in dataset.")
    
    try:
        logger.info(f"Loading Ridge Regression model and dataset for Lattice Parameters ({target_col_ridge}) prediction...")
        ridge_model = load_model(ridge_model_path)
        X_ridge, y_ridge, feature_names_ridge = load_dataset_features_and_targets(dataset_path, target_col=target_col_ridge)
        
        # Verify feature names match (they should if same dataset)
        if feature_names != feature_names_ridge:
            logger.warning("Feature names mismatch between RF and Ridge datasets? Using Ridge set.")
            feature_names = feature_names_ridge
        
        shap_ridge_result = compute_shap_ridge(X_ridge, y_ridge, ridge_model, feature_names)
        results["ridge_regression_lattice"] = shap_ridge_result
        logger.info("Completed SHAP analysis for Ridge Regression (Lattice Parameters).")
        
    except Exception as e:
        logger.error(f"Failed to compute SHAP for Ridge Regression: {e}", exc_info=True)
        results["ridge_regression_lattice"] = {"error": str(e)}
    
    # Save unified results
    logger.info(f"Saving SHAP analysis results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("T023 completed successfully.")
    return results

if __name__ == "__main__":
    main()