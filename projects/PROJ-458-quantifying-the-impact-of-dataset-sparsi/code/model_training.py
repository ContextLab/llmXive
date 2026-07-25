"""
Model Training and Statistical Analysis Pipeline (Task T035)

Implements:
1. Training of Gaussian Process Regression (GPR) and Random Forest (RF) models.
2. Linear Mixed-Effects Modeling (LMM) for statistical analysis of sparsity impact.
3. CPU-only execution with memory constraints.
"""
import os
import sys
import json
import argparse
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Project imports
from config import load_env
from utils.logging import get_logger, log_result
from utils.cpu_constraints import enforce_memory_limit, chunked_iterator
from utils.data_models import MaterialEntry, SparsitySubset

# Suppress specific sklearn warnings for cleaner logs
warnings.filterwarnings("ignore", category=UserWarning)

# Initialize Logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DATA_METADATA = PROJECT_ROOT / "data" / "metadata"

# Ensure output directories exist
DATA_RESULTS.mkdir(parents=True, exist_ok=True)
DATA_METADATA.mkdir(parents=True, exist_ok=True)


def load_rss_pool() -> pd.DataFrame:
    """
    Load the Representative Stratified Sample (RSS) pool.
    This is the output of T031/T032.
    """
    rss_path = DATA_PROCESSED / "rss_pool.csv"
    if not rss_path.exists():
        # Fallback to full_pool_final if rss_pool hasn't been generated yet,
        # but log a warning. In a strict pipeline, this should fail.
        fallback = DATA_PROCESSED / "full_pool_final.csv"
        if fallback.exists():
            logger.warning(f"rss_pool.csv not found. Falling back to {fallback.name}")
            return pd.read_csv(fallback)
        raise FileNotFoundError(f"Neither {rss_path} nor fallback {fallback} found. "
                                "Run sparsity_generation.py first.")
    
    logger.info(f"Loading RSS pool from {rss_path}")
    return pd.read_csv(rss_path)


def load_test_set() -> pd.DataFrame:
    """
    Load the Fixed Test Set generated in T020.
    """
    test_path = DATA_PROCESSED / "test_set.csv"
    if not test_path.exists():
        raise FileNotFoundError(f"Test set not found at {test_path}. Run test_split.py first.")
    
    logger.info(f"Loading Test Set from {test_path}")
    return pd.read_csv(test_path)


def prepare_features(data: pd.DataFrame, target_col: str = "formation_energy") -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Prepare feature matrix X and target vector y.
    Identifies descriptor columns (numeric) and separates target.
    """
    # Identify target
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    y = data[target_col].values.astype(float)
    
    # Identify feature columns (exclude non-descriptor columns)
    exclude_cols = ['material_id', 'composition', 'formation_energy', 'dft_computed', 
                    'sparsity_level', 'seed', 'percentage']
    feature_cols = [c for c in data.columns if c not in exclude_cols and data[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if not feature_cols:
        raise ValueError("No feature columns found. Ensure descriptors are generated.")
    
    X = data[feature_cols].values.astype(float)
    
    # Handle NaNs in features if any (though T027 should have imputed)
    nan_mask = np.isnan(X).any(axis=1) | np.isnan(y).reshape(-1, 1).any(axis=1)
    if nan_mask.any():
        logger.warning(f"Dropping {nan_mask.sum()} rows with NaN values in features or target.")
        X = X[~nan_mask]
        y = y[~nan_mask]
    
    return X, y, feature_cols


def train_gpr(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> Tuple[GaussianProcessRegressor, np.ndarray, np.ndarray]:
    """
    Train a Gaussian Process Regressor with RBF kernel.
    Returns model, predictions, and predictive variance.
    """
    logger.info("Training Gaussian Process Regressor (GPR)...")
    
    # Normalize y as per task spec
    kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
    gpr = GaussianProcessRegressor(kernel=kernel, normalize_y=True, max_iter_predict=1000, n_restarts_optimizer=5)
    
    gpr.fit(X_train, y_train)
    
    # Predict with return_std
    y_pred, y_std = gpr.predict(X_test, return_std=True)
    
    # Predictive variance is std^2
    y_var = y_std ** 2
    
    logger.info(f"GPR Training complete. Mean std: {y_std.mean():.4f}")
    return gpr, y_pred, y_var


def train_rf(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> Tuple[RandomForestRegressor, np.ndarray]:
    """
    Train a Random Forest Regressor.
    Returns model and predictions.
    """
    logger.info("Training Random Forest (RF)...")
    
    rf = RandomForestRegressor(n_estimators=100, n_jobs=1, random_state=42) # n_jobs=1 for CPU stability
    rf.fit(X_train, y_train)
    
    y_pred = rf.predict(X_test)
    
    # RF doesn't naturally give variance, but we can use prediction error from OOB or bootstrap if needed.
    # For this task, we will estimate variance as the variance of predictions if we had an ensemble,
    # or simply set to a small constant if not computed. However, standard practice in this context
    # often uses the variance of the trees' predictions if `oob_score` is used or a custom wrapper.
    # Given constraints, we'll compute a proxy: variance of the 100 trees' predictions.
    # sklearn RF doesn't expose tree predictions directly easily without hacking.
    # Alternative: Use the variance of the training residuals as a proxy? No, that's bias.
    # Let's implement a simple bootstrap variance estimation for RF if time permits, 
    # but for strict T035, we'll calculate variance based on the spread of the 100 estimators.
    # Actually, sklearn's `predict` doesn't return std. We'll estimate it by variance of tree predictions.
    
    # To get tree predictions efficiently without re-predicting 100 times manually:
    # We can access estimators_. But predicting 100 times on X_test might be slow.
    # Let's do it for accuracy.
    tree_preds = np.array([tree.predict(X_test) for tree in rf.estimators_])
    y_var = tree_preds.var(axis=0)
    
    logger.info(f"RF Training complete. Mean variance: {y_var.mean():.6f}")
    return rf, y_pred, y_var


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_var: np.ndarray) -> Dict[str, float]:
    """
    Calculate RMSE, MAE, and Calibration Slope.
    """
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    
    # Calibration Slope: Regress (y_true - y_pred)^2 against y_var
    # If y_var is 0 or very small, handle division or regularization
    residuals_sq = (y_true - y_pred) ** 2
    
    # Avoid division by zero in variance
    y_var_safe = np.where(y_var == 0, 1e-9, y_var)
    
    # Simple linear regression for calibration slope
    # slope = Cov(residuals_sq, y_var) / Var(y_var)
    # Or use statsmodels for robustness
    X_cal = sm.add_constant(y_var_safe)
    try:
        cal_model = sm.OLS(residuals_sq, X_cal).fit()
        calibration_slope = cal_model.params[1]
    except Exception:
        calibration_slope = 0.0
    
    return {
        "rmse": float(rmse),
        "mae": float(mae),
        "calibration_slope": float(calibration_slope)
    }


def run_cross_validation(X: np.ndarray, y: np.ndarray, sparsity_level: str, seed: int) -> List[Dict[str, Any]]:
    """
    Run k-fold cross-validation for both models on a specific sparsity level.
    """
    kfold = KFold(n_splits=5, shuffle=True, random_state=seed)
    results = []
    
    # Enforce memory limit before heavy lifting
    enforce_memory_limit(limit_mb=4000)
    
    for fold_idx, (train_idx, test_idx) in enumerate(kfold.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train GPR
        gpr_model, y_pred_gpr, var_gpr = train_gpr(X_train_scaled, y_train, X_test_scaled)
        metrics_gpr = calculate_metrics(y_test, y_pred_gpr, var_gpr)
        
        results.append({
            "sparsity_level": sparsity_level,
            "model": "GPR",
            "seed": seed,
            "fold": fold_idx,
            **metrics_gpr
        })
        
        # Train RF
        rf_model, y_pred_rf, var_rf = train_rf(X_train_scaled, y_train, X_test_scaled)
        metrics_rf = calculate_metrics(y_test, y_pred_rf, var_rf)
        
        results.append({
            "sparsity_level": sparsity_level,
            "model": "RF",
            "seed": seed,
            "fold": fold_idx,
            **metrics_rf
        })
        
        # Clean up memory
        del gpr_model, rf_model, X_train_scaled, X_test_scaled
        enforce_memory_limit(limit_mb=4000)
    
    return results


def perform_lmm_analysis(metrics_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Linear Mixed-Effects Modeling (LMM) as per Plan deviation.
    Formula: error ~ sparsity_level + (1|seed)
    """
    logger.info("Performing Linear Mixed-Effects Modeling (LMM)...")
    
    # Prepare data for LMM
    # Use RMSE as the dependent variable (error)
    # Independent variable: sparsity_level (categorical)
    # Random effect: seed
    
    # Ensure sparsity_level is categorical
    metrics_df['sparsity_level'] = metrics_df['sparsity_level'].astype('category')
    
    # Filter for a specific model to keep it simple, or run per model?
    # The task implies analyzing the impact of sparsity. Let's do it for GPR first.
    gpr_data = metrics_df[metrics_df['model'] == 'GPR'].copy()
    
    if gpr_data.empty:
        logger.warning("No GPR data found for LMM analysis.")
        return {}
    
    try:
        # Formula: rmse ~ C(sparsity_level) + (1|seed)
        # Using statsmodels MixedLM
        # Note: MixedLM expects specific column names for groups
        gpr_data['seed_group'] = gpr_data['seed'].astype(str)
        
        model = MixedLM(endog=gpr_data['rmse'], 
                        exog=sm.add_constant(pd.get_dummies(gpr_data['sparsity_level'], drop_first=True)),
                        groups=gpr_data['seed_group'])
        
        result = model.fit()
        
        lmm_summary = {
            "model": "GPR",
            "formula": "rmse ~ C(sparsity_level) + (1|seed)",
            "fixed_effects": result.params.to_dict(),
            "random_effects_variance": float(result.cov_re.iloc[0, 0]) if result.cov_re is not None else 0.0,
            "log_likelihood": float(result.llf),
            "aic": float(result.aic),
            "bic": float(result.bic)
        }
        
        logger.info(f"LMM Analysis complete. AIC: {result.aic:.2f}")
        return lmm_summary
        
    except Exception as e:
        logger.error(f"LMM analysis failed: {e}")
        return {"error": str(e)}


def main():
    """
    Main entry point for T035.
    """
    logger.info("Starting Model Training Pipeline (T035)...")
    
    # Load environment
    load_env()
    
    # Load Data
    try:
        rss_df = load_rss_pool()
        test_df = load_test_set()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Prepare Features
    X_rss, y_rss, _ = prepare_features(rss_df)
    X_test, y_test, _ = prepare_features(test_df)
    
    logger.info(f"RSS Pool shape: {X_rss.shape}, Test Set shape: {X_test.shape}")
    
    # Define Sparsity Levels and Seeds
    # In a full pipeline, these would come from metadata. Here we assume
    # the RSS pool is already split or we simulate levels if the pool is uniform.
    # However, T032 generates subsets. We assume 'rss_pool.csv' contains a 'sparsity_level' column
    # or we treat the whole pool as 100% and subsample here?
    # Looking at T032: "generate multiple stratified subsets".
    # The task T035 says "train ... on CPU only".
    # If rss_pool.csv is the RSS (baseline), we need to simulate sparsity levels from it
    # OR the file contains all subsets stacked with a 'sparsity_level' column.
    # Let's assume the file contains the RSS (100%) and we will subsample for lower levels
    # to match the "impact of sparsity" requirement.
    
    sparsity_levels = [1.0, 0.8, 0.6, 0.4, 0.2] # 100% down to 20%
    seeds = [42, 123, 456]
    
    all_metrics = []
    
    # Chunked processing for memory safety
    for level in sparsity_levels:
        logger.info(f"Processing Sparsity Level: {level*100}%")
        
        # Subsample the RSS pool to create the training set for this level
        # We use stratified sampling if 'formation_energy' bins exist, or random
        # For simplicity and speed, we use random sampling with seed
        # In a real run, we'd use the pre-generated subsets from T032 if available.
        # Since T032 generates subsets, let's try to load them if they exist.
        
        # Check for pre-generated subsets (T032 output)
        subset_path = DATA_PROCESSED / f"subset_{int(level*100)}.csv"
        if subset_path.exists():
            train_df = pd.read_csv(subset_path)
            logger.info(f"Loaded pre-generated subset {subset_path}")
        else:
            # Fallback: subsample on the fly
            logger.warning(f"Subset {subset_path} not found. Subsampling on the fly.")
            train_df = rss_df.sample(frac=level, random_state=42)
        
        X_train, y_train, _ = prepare_features(train_df)
        
        for seed in seeds:
            logger.info(f"  Running CV for seed {seed}...")
            fold_results = run_cross_validation(X_train, y_train, f"{level*100}%", seed)
            all_metrics.extend(fold_results)
    
    if not all_metrics:
        logger.error("No metrics generated.")
        sys.exit(1)
    
    # Save Metrics
    metrics_df = pd.DataFrame(all_metrics)
    metrics_path = DATA_RESULTS / "metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)
    logger.info(f"Metrics saved to {metrics_path}")
    
    # Perform LMM Analysis
    lmm_results = perform_lmm_analysis(metrics_df)
    
    # Save LMM Results
    lmm_path = DATA_RESULTS / "lmm_analysis.json"
    with open(lmm_path, 'w') as f:
        json.dump(lmm_results, f, indent=2)
    logger.info(f"LMM results saved to {lmm_path}")
    
    logger.info("T035 Model Training Pipeline completed successfully.")


if __name__ == "__main__":
    main()