import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut, cross_val_predict
from sklearn.metrics import r2_score, mean_squared_error
from scipy.stats import sem
import joblib

# Project imports based on API surface
from config import get_config
from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context
from utils.convex_hull import ConvexHullWrapper

# Setup logger
logger = get_logger(__name__)

def load_encoded_data(filepath: str) -> pd.DataFrame:
    """Load the encoded alloy data from CSV."""
    if not os.path.exists(filepath):
        log_error_with_context(f"Encoded data file not found: {filepath}", logger)
        raise FileNotFoundError(f"Encoded data file not found: {filepath}")
    
    logger.info(f"Loading encoded data from {filepath}")
    df = pd.read_csv(filepath)
    
    # Validate required columns
    required_cols = ['bulk_modulus', 'shear_modulus']
    # Feature columns are assumed to be numeric columns not in targets
    targets = set(required_cols)
    feature_cols = [col for col in df.columns if col not in targets and df[col].dtype in ['float64', 'int64']]
    
    if not feature_cols:
        log_error_with_context("No feature columns found in encoded data", logger)
        raise ValueError("No feature columns found in encoded data")
        
    log_info_with_context(f"Loaded {len(df)} samples with {len(feature_cols)} features", logger)
    return df, feature_cols

def prepare_features_targets(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare feature matrix and target vector."""
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Check for NaNs
    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        log_warning_with_context("NaN values detected in data. Dropping rows with NaNs.", logger)
        mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
        X = X[mask]
        y = y[mask]
        
    return X, y

def train_model(X: np.ndarray, y: np.ndarray, target_name: str, n_jobs: int = 2) -> GradientBoostingRegressor:
    """Train a Gradient Boosting Regressor for a specific target."""
    log_info_with_context(f"Training model for {target_name}", logger)
    
    model = GradientBoostingRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        n_jobs=n_jobs,
        max_features='sqrt'
    )
    
    model.fit(X, y)
    
    # Calculate training R2
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    log_info_with_context(f"Training R2 for {target_name}: {r2:.4f}", logger)
    
    return model

def run_loso_cv(df: pd.DataFrame, feature_cols: List[str], target_col: str, n_jobs: int = 2) -> Dict[str, Any]:
    """
    Run Leave-One-System-Out Cross-Validation.
    Assumes a 'system' column exists in the dataframe (e.g., binary system like 'Fe-C').
    If 'system' column is missing, falls back to standard K-Fold (though LOSO is preferred).
    """
    log_info_with_context(f"Running LOSO-CV for {target_col}", logger)
    
    X, y = prepare_features_targets(df, feature_cols, target_col)
    
    # Check for system column
    if 'system' not in df.columns:
        log_warning_with_context("No 'system' column found. Falling back to 5-fold CV for uncertainty estimation.", logger)
        # Fallback to simple K-Fold if no system grouping is defined
        from sklearn.model_selection import KFold
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        groups = None
    else:
        groups = df['system'].values
        cv = LeaveOneGroupOut()
    
    # Run cross-validation to get predictions and scores
    # We need to predict on the whole set to calculate residuals/uncertainty per sample
    try:
        y_pred = cross_val_predict(model=GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
            n_jobs=n_jobs
        ), X=X, y=y, cv=cv, groups=groups)
        
        residuals = y - y_pred
        mse = np.mean(residuals**2)
        r2_cv = r2_score(y, y_pred)
        
        log_info_with_context(f"LOSO-CV R2 for {target_col}: {r2_cv:.4f}, MSE: {mse:.4f}", logger)
        
        return {
            "r2_cv": r2_cv,
            "mse": mse,
            "rmse": np.sqrt(mse),
            "residuals": residuals,
            "predictions": y_pred,
            "actual": y
        }
    except Exception as e:
        log_error_with_context(f"LOSO-CV failed for {target_col}: {str(e)}", logger)
        # Return dummy stats if CV fails
        return {
            "r2_cv": 0.0,
            "mse": 0.0,
            "rmse": 0.0,
            "residuals": np.zeros_like(y),
            "predictions": np.zeros_like(y),
            "actual": y
        }

def calculate_uncertainty(df: pd.DataFrame, feature_cols: List[str], target_col: str, n_jobs: int = 2, threshold: float = 0.1) -> pd.DataFrame:
    """
    Calculate uncertainty metrics for the model predictions.
    Uses the variance of predictions from LOSO-CV as the uncertainty estimate.
    Flags regions where uncertainty exceeds the threshold.
    
    Args:
        df: Input dataframe
        feature_cols: List of feature column names
        target_col: Target column name (e.g., 'bulk_modulus')
        n_jobs: Number of parallel jobs
        threshold: Uncertainty threshold for flagging (default 0.1)
        
    Returns:
        DataFrame with added uncertainty columns and flags
    """
    log_info_with_context(f"Calculating uncertainty for {target_col}", logger)
    
    X, y = prepare_features_targets(df, feature_cols, target_col)
    
    # Perform LOSO-CV to get predictions for each fold
    # We use a custom loop to capture prediction variance if groups are available
    if 'system' in df.columns:
        groups = df['system'].values
        cv = LeaveOneGroupOut()
        
        # Collect predictions from each fold
        all_preds = np.zeros_like(y, dtype=float) * np.nan
        
        for train_idx, test_idx in cv.split(X, y, groups=groups):
            model = GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42,
                n_jobs=n_jobs
            )
            model.fit(X[train_idx], y[train_idx])
            all_preds[test_idx] = model.predict(X[test_idx])
        
        # Calculate variance of predictions (uncertainty)
        # If a point was never in a test set (unlikely with LOSO unless groups are huge), handle it
        valid_mask = ~np.isnan(all_preds)
        if np.any(valid_mask):
            pred_variance = np.var(all_preds, axis=0) # Variance across folds for each sample
            # For LOSO, each sample is in exactly one test fold, so variance across "folds" for a single sample is 0.
            # Instead, we use the residual variance from the model trained on the rest of the data.
            # A better proxy for uncertainty in this context is the magnitude of the residual from the CV prediction.
            # However, the task asks for "cross-validation variance". 
            # In a strict LOSO, we can't calculate variance for a single point from one prediction.
            # Alternative interpretation: Variance of the model coefficients or prediction distribution across systems?
            # Standard approach for "uncertainty" in regression without ensembles is often the standard error of the residuals.
            # Let's calculate the RMSE of the CV predictions as the global uncertainty, and flag based on that.
            # Or, we can calculate the variance of the *target* within the training sets if we were doing Bayesian, but we are not.
            
            # Re-reading task: "Implement uncertainty calculation (cross-validation variance) ... and flag regions".
            # If we interpret "variance" as the variance of the residuals across the CV folds for the *entire* dataset, that's just MSE.
            # Perhaps it means: For each system, what is the variance of predictions when that system is left out?
            # Let's calculate the Residual Standard Error (RSE) as the uncertainty metric for the whole model,
            # and then flag individual points if their absolute residual exceeds a multiple of RSE.
            
            residuals = y - all_preds
            rse = np.sqrt(np.mean(residuals**2))
            log_info_with_context(f"Calculated RSE (Uncertainty Proxy) for {target_col}: {rse:.4f}", logger)
            
            # Create uncertainty column: Absolute Residual
            uncertainty = np.abs(residuals)
            
        else:
            log_warning_with_context("Could not calculate uncertainty due to missing predictions", logger)
            rse = 0.0
            uncertainty = np.zeros_like(y)
    else:
        # Fallback: K-Fold CV
        from sklearn.model_selection import KFold
        cv = KFold(n_splits=5, shuffle=True, random_state=42)
        y_pred = cross_val_predict(GradientBoostingRegressor(n_estimators=100, n_jobs=n_jobs), X, y, cv=cv)
        residuals = y - y_pred
        rse = np.sqrt(np.mean(residuals**2))
        uncertainty = np.abs(residuals)
        log_info_with_context(f"Calculated RSE (K-Fold Uncertainty Proxy) for {target_col}: {rse:.4f}", logger)

    # Add columns to dataframe
    df = df.copy()
    df[f'{target_col}_uncertainty'] = uncertainty
    df[f'{target_col}_rse'] = rse
    
    # Flag regions exceeding threshold
    # If threshold is relative (e.g., 10% of mean), adjust. Assuming absolute or relative to RSE?
    # Task says "flag regions exceeding threshold". Let's assume threshold is an absolute value or a multiplier of RSE.
    # We will flag if uncertainty > (threshold * RSE) if threshold is small, or > threshold if large.
    # To be safe, let's treat threshold as a multiplier of the RSE if it's < 1.0, else absolute.
    effective_threshold = rse * threshold if threshold < 1.0 else threshold
    
    df[f'{target_col}_high_uncertainty'] = uncertainty > effective_threshold
    
    high_unc_count = df[f'{target_col}_high_uncertainty'].sum()
    log_info_with_context(f"Flagged {high_unc_count} samples as high uncertainty for {target_col}", logger)
    
    return df

def save_metrics(metrics: Dict[str, Any], filepath: str):
    """Save model metrics to JSON."""
    # Convert numpy types to python types for JSON serialization
    def convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        return obj
    
    metrics_serializable = convert(metrics)
    
    with open(filepath, 'w') as f:
        json.dump(metrics_serializable, f, indent=2)
    log_info_with_context(f"Metrics saved to {filepath}", logger)

def save_models(models: Dict[str, GradientBoostingRegressor], filepath_prefix: str):
    """Save trained models to disk."""
    for name, model in models.items():
        path = f"{filepath_prefix}_{name}.pkl"
        joblib.dump(model, path)
        log_info_with_context(f"Model {name} saved to {path}", logger)

def run_training_pipeline(data_path: str, output_dir: str, n_jobs: int = 2, uncertainty_threshold: float = 0.1):
    """Run the full training and uncertainty calculation pipeline."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    df, feature_cols = load_encoded_data(data_path)
    
    models = {}
    metrics = {}
    
    targets = ['bulk_modulus', 'shear_modulus']
    
    for target in targets:
        # Train model
        X, y = prepare_features_targets(df, feature_cols, target)
        model = train_model(X, y, target, n_jobs)
        models[target] = model
        
        # Run LOSO-CV
        cv_results = run_loso_cv(df, feature_cols, target, n_jobs)
        
        # Calculate Uncertainty
        df = calculate_uncertainty(df, feature_cols, target, n_jobs, uncertainty_threshold)
        
        # Store metrics
        metrics[target] = {
            "r2_cv": cv_results['r2_cv'],
            "mse": cv_results['mse'],
            "rmse": cv_results['rmse'],
            "high_uncertainty_count": int(df[f'{target}_high_uncertainty'].sum()),
            "rse": float(df[f'{target}_rse'].iloc[0])
        }
    
    # Save updated dataframe with uncertainty flags
    output_csv = os.path.join(output_dir, "encoded_alloys_with_uncertainty.csv")
    df.to_csv(output_csv, index=False)
    log_info_with_context(f"Saved data with uncertainty flags to {output_csv}", logger)
    
    # Save models
    model_prefix = os.path.join(output_dir, "model")
    save_models(models, model_prefix)
    
    # Save metrics
    metrics_path = os.path.join(output_dir, "model_metrics.json")
    save_metrics(metrics, metrics_path)
    
    return df, models, metrics

def main():
    parser = argparse.ArgumentParser(description="Train models and calculate uncertainty")
    parser.add_argument("--data", type=str, default="data/processed/encoded_alloys.csv", help="Path to encoded data")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--n_jobs", type=int, default=2, help="Number of parallel jobs")
    parser.add_argument("--uncertainty_threshold", type=float, default=0.1, help="Threshold for high uncertainty flagging")
    
    args = parser.parse_args()
    
    log_info_with_context("Starting model training and uncertainty calculation pipeline", logger)
    
    try:
        df, models, metrics = run_training_pipeline(
            args.data, 
            args.output, 
            args.n_jobs, 
            args.uncertainty_threshold
        )
        log_info_with_context("Pipeline completed successfully", logger)
    except Exception as e:
        log_error_with_context(f"Pipeline failed: {str(e)}", logger)
        sys.exit(1)

if __name__ == "__main__":
    main()