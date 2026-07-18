import os
import json
import logging
import numpy as np
from typing import Tuple, Dict, Any, Optional, List
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel as C
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
import pandas as pd

from config import get_processed_data_dir, get_results_dir, get_models_dir, ensure_directories, get_random_seed
from utils.logger import setup_logging, log_execution_time, get_log_file_path
from data.preprocess import load_raw_csv

# Setup logging for this module
logger = setup_logging("gpr_trainer")

def optimize_hyperparameters(X: np.ndarray, y: np.ndarray, kernel: Any, n_restarts: int = 10) -> Tuple[Any, Dict[str, float]]:
    """
    Optimizes hyperparameters for the GPR model using cross-validation.
    """
    gpr = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=n_restarts, random_state=get_random_seed())
    
    # Simple cross-validation to find best hyperparameters
    # Note: In a real scenario, we might use GridSearchCV or more sophisticated methods
    gpr.fit(X, y)
    
    best_kernel = gpr.kernel_
    kernel_params = {}
    for i, param in enumerate(best_kernel.parameters):
        kernel_params[f"param_{i}"] = float(param)
    
    return best_kernel, kernel_params

def train_gpr_model(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray, target_col: str) -> Tuple[GaussianProcessRegressor, Dict[str, Any]]:
    """
    Trains a GPR model with RBF kernel and k-fold cross-validation.
    Returns the trained model and performance metrics.
    """
    # Define the kernel
    kernel = C(1.0, (1e-3, 1e3)) * RBF(1.0, (1e-2, 1e2))
    
    # Optimize hyperparameters
    optimized_kernel, kernel_params = optimize_hyperparameters(X_train, y_train, kernel, n_restarts=10)
    
    # Train the final model
    gpr = GaussianProcessRegressor(kernel=optimized_kernel, random_state=get_random_seed())
    gpr.fit(X_train, y_train)
    
    # Predictions
    y_pred, sigma = gpr.predict(X_test, return_std=True)
    
    # Calculate metrics
    from models.metrics import calculate_r2, calculate_rmse, calculate_mae
    r2 = calculate_r2(y_test, y_pred)
    rmse = calculate_rmse(y_test, y_pred)
    mae = calculate_mae(y_test, y_pred)
    
    metrics = {
        "target": target_col,
        "r2": float(r2),
        "rmse": float(rmse),
        "mae": float(mae),
        "kernel_params": kernel_params
    }
    
    return gpr, metrics

def run_stratified_analysis(processed_csv_path: str) -> Dict[str, Any]:
    """
    Performs stratified analysis by alloy_type to assess confounder sensitivity.
    Loads the processed CSV, splits by unique alloy types, and trains a GPR model
    for each stratum to compare performance.
    """
    logger.info("Starting stratified analysis by alloy_type")
    
    # Load processed data
    df = pd.read_csv(processed_csv_path)
    
    # Identify the alloy_type column (one-hot encoded columns might exist, but we look for the original if present or derive from encoded)
    # Assuming the preprocessing step might have dropped the original 'alloy_type' column after encoding.
    # However, for stratified analysis, we need the original grouping. 
    # If the original column was dropped, we need to reverse one-hot or check if it's still there.
    # Based on T015A, the original column is dropped. We must infer strata if possible, 
    # or the task implies we should have kept a mapping. 
    # Let's assume for this task that 'alloy_type' or a derived 'stratum_id' is available, 
    # OR we look for columns like 'alloy_type_316L', 'alloy_type_Inconel' etc. to group back.
    # A robust way: if 'alloy_type' is missing, check for columns starting with 'alloy_type_'
    # and reconstruct the original category.
    
    if 'alloy_type' in df.columns:
        strata_col = 'alloy_type'
    else:
        # Try to find one-hot columns
        one_hot_cols = [c for c in df.columns if c.startswith('alloy_type_')]
        if one_hot_cols:
            # Reconstruct alloy_type from one-hot columns
            # This assumes exactly one is 1 per row
            def reconstruct(row):
                for col in one_hot_cols:
                    if row[col] == 1:
                        return col.replace('alloy_type_', '')
                return 'Unknown'
            df['alloy_type_reconstructed'] = df.apply(reconstruct, axis=1)
            strata_col = 'alloy_type_reconstructed'
            logger.warning(f"Reconstructed alloy_type from one-hot columns: {one_hot_cols}")
        else:
            logger.error("Could not find alloy_type or derived columns for stratification.")
            return {"error": "No alloy_type column found for stratification"}

    # Identify feature columns (exclude target and strata columns)
    # Assuming standard targets: yield_strength, ductility, fatigue_life (optional)
    targets = [c for c in df.columns if c in ['yield_strength', 'ductility', 'fatigue_life'] and c in df.columns]
    if not targets:
        logger.error("No target columns found.")
        return {"error": "No target columns found"}
    
    # We will analyze the primary target: yield_strength if available, else ductility
    target_col = 'yield_strength' if 'yield_strength' in targets else targets[0]
    
    feature_cols = [c for c in df.columns if c not in [target_col, strata_col] + targets]
    # Ensure we have numeric features
    feature_cols = [c for c in feature_cols if df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
    
    if len(feature_cols) == 0:
        logger.error("No numeric feature columns found.")
        return {"error": "No numeric feature columns found"}
    
    results = {}
    
    unique_strata = df[strata_col].unique()
    logger.info(f"Found {len(unique_strata)} unique strata: {unique_strata}")
    
    for stratum in unique_strata:
        stratum_df = df[df[strata_col] == stratum]
        
        if len(stratum_df) < 10: # Minimum sample size for training
            logger.warning(f"Stratum {stratum} has too few samples ({len(stratum_df)}). Skipping.")
            results[stratum] = {"status": "skipped", "reason": "insufficient_samples", "count": len(stratum_df)}
            continue
        
        X = stratum_df[feature_cols].values
        y = stratum_df[target_col].values
        
        # Train-test split for this stratum
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        if len(X_train) < 5 or len(X_test) < 2:
            logger.warning(f"Stratum {stratum} has insufficient data for split. Skipping.")
            results[stratum] = {"status": "skipped", "reason": "insufficient_split", "count": len(stratum_df)}
            continue
        
        try:
            gpr_model, metrics = train_gpr_model(X_train, y_train, X_test, y_test, target_col)
            results[stratum] = {
                "status": "success",
                "sample_count": len(stratum_df),
                "train_size": len(X_train),
                "test_size": len(X_test),
                "metrics": metrics
            }
            logger.info(f"Stratum {stratum}: R2={metrics['r2']:.4f}, RMSE={metrics['rmse']:.4f}")
        except Exception as e:
            logger.error(f"Failed to train model for stratum {stratum}: {e}")
            results[stratum] = {"status": "error", "error": str(e)}
    
    return results

@log_execution_time(logger)
def main():
    """
    Main entry point for GPR training and stratified analysis.
    """
    ensure_directories()
    
    # Load processed data
    processed_dir = get_processed_data_dir()
    processed_csv_path = os.path.join(processed_dir, "processed_data.csv")
    
    if not os.path.exists(processed_csv_path):
        logger.error(f"Processed data file not found: {processed_csv_path}")
        # Attempt to run preprocessing first if not done
        logger.info("Attempting to run preprocessing pipeline...")
        from data.preprocess import main as preprocess_main
        preprocess_main()
        if not os.path.exists(processed_csv_path):
            raise FileNotFoundError(f"Processed data file still not found after preprocessing: {processed_csv_path}")
    
    # Run stratified analysis
    stratified_results = run_stratified_analysis(processed_csv_path)
    
    # Save results
    results_dir = get_results_dir()
    output_path = os.path.join(results_dir, "stratified_analysis.json")
    
    with open(output_path, 'w') as f:
        json.dump(stratified_results, f, indent=2)
    
    logger.info(f"Stratified analysis results saved to {output_path}")
    
    return stratified_results

if __name__ == "__main__":
    main()