import os
import sys
import json
import pickle
import argparse
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import ttest_rel
from statsmodels.stats.power import TTestPower
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from utils.config import get_config

logger = get_logger(__name__)

def load_processed_data(filepath: str) -> pd.DataFrame:
    """Load the processed descriptors CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    logger.info(f"Loading processed data from {filepath}")
    df = pd.read_csv(filepath)
    # Ensure numeric types for calculation
    numeric_cols = ['mean_atomic_radius', 'electronegativity_variance', 
                    'valence_electron_count', 'hume_rothery_concentration', 'temperature']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def train_random_forest(X: np.ndarray, y: np.ndarray, random_state: int = 42) -> RandomForestRegressor:
    """Train a Random Forest Regressor."""
    logger.info("Training Random Forest model...")
    model = RandomForestRegressor(
        n_estimators=100, 
        max_depth=10, 
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    logger.info("Random Forest model trained successfully.")
    return model

def run_loso_cv(df: pd.DataFrame, model: RandomForestRegressor) -> Dict[str, Any]:
    """Run Leave-One-System-Out Cross-Validation."""
    logger.info("Running Leave-One-System-Out Cross-Validation...")
    
    # Ensure 'system_id' column exists
    if 'system_id' not in df.columns:
        raise ValueError("DataFrame must contain 'system_id' column for LOSO.")
    
    logo = LeaveOneGroupOut()
    fold_results = []
    
    X = df[['mean_atomic_radius', 'electronegativity_variance', 
            'valence_electron_count', 'hume_rothery_concentration']].values
    y = df['temperature'].values
    groups = df['system_id'].values
    
    # Check for NaNs in target or features
    valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
    X = X[valid_mask]
    y = y[valid_mask]
    groups = groups[valid_mask]
    
    if len(X) == 0:
        raise ValueError("No valid data points remaining after NaN filtering.")
    
    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        test_groups = groups[test_idx]
        
        # Train on fold
        fold_model = train_random_forest(X_train, y_train)
        
        # Predict
        y_pred = fold_model.predict(X_test)
        
        # Metrics
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        fold_results.append({
            "test_systems": list(np.unique(test_groups)),
            "mae": mae,
            "r2": r2,
            "n_train": len(train_idx),
            "n_test": len(test_idx)
        })
        
        logger.info(f"Fold completed: Systems {np.unique(test_groups)}, MAE={mae:.2f}, R2={r2:.4f}")
    
    return {
        "method": "LOSO",
        "fold_results": fold_results,
        "aggregated_mae": np.mean([f['mae'] for f in fold_results]),
        "aggregated_r2": np.mean([f['r2'] for f in fold_results])
    }

def perform_power_analysis(df: pd.DataFrame, loso_results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Perform statistical power analysis and generate a detailed report.
    Returns (success, report_string).
    """
    logger.info("Performing statistical power analysis...")
    
    # We need a baseline to compare against. Assuming a Null Model (Global Mean) exists
    # or calculating one dynamically for the power analysis context.
    # For this task, we calculate the variance of the target variable to estimate effect size.
    # In a real scenario, we would compare RF MAE vs Null MAE.
    
    y = df['temperature'].values
    y = y[~np.isnan(y)]
    
    if len(y) < 2:
        raise ValueError("Insufficient data points for power analysis.")
    
    # Estimate effect size (Cohen's d) based on standard deviation of y
    # Assuming we want to detect a difference of 1 standard deviation (d=1.0) as a "significant" improvement
    # or we use the observed variance in the LOSO results.
    # Here we use the observed variance of the target to estimate required sample size.
    std_y = np.std(y)
    mean_y = np.mean(y)
    
    # Effect size assumption: We want to detect a reduction in MAE by 10% of the std dev
    # This is a heuristic for power analysis in regression contexts.
    target_effect_size = 0.1 * std_y / std_y  # Cohen's d = 0.1 (small effect)
    
    # Calculate power for current sample size
    # We use TTestPower for a simplified approximation of the power to detect a mean difference
    # between folds or against a baseline.
    sample_size = len(y)
    alpha = 0.05
    
    power_analyzer = TTestPower()
    try:
        power = power_analyzer.power(effect_size=target_effect_size, nobs1=sample_size, alpha=alpha)
    except Exception as e:
        log_error(f"Power calculation failed: {e}")
        power = 0.0
    
    # Detailed Report Generation
    report_lines = [
        "=== Statistical Power Analysis Report ===",
        f"Target Power Threshold: 0.80",
        f"Calculated Power: {power:.4f}",
        f"Effect Size (Cohen's d): {target_effect_size:.4f}",
        f"Sample Size (N): {sample_size}",
        f"Alpha Level: {alpha}",
        f"Target Variable Mean: {mean_y:.2f}",
        f"Target Variable Std Dev: {std_y:.2f}",
        "-----------------------------------------"
    ]
    
    report_str = "\n".join(report_lines)
    
    if power < 0.8:
        error_msg = f"{ErrorCode.INSUFFICIENT_POWER.value}: {report_str}"
        log_error(error_msg)
        return False, error_msg
    
    log_info(f"Power analysis passed. Power: {power:.4f}")
    return True, report_str

def save_model(model: Any, filepath: str) -> None:
    """Save the trained model to disk."""
    logger.info(f"Saving model to {filepath}")
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    logger.info("Model saved successfully.")

def save_report(results: Dict[str, Any], filepath: str) -> None:
    """Save the evaluation report to disk."""
    logger.info(f"Saving report to {filepath}")
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info("Report saved successfully.")

def main():
    parser = argparse.ArgumentParser(description="Train Random Forest Model with Power Analysis")
    parser.add_argument("--input", type=str, required=True, help="Path to processed descriptors CSV")
    parser.add_argument("--output-model", type=str, default="data/artifacts/model.pkl", help="Path to save model")
    parser.add_argument("--output-report", type=str, default="data/artifacts/evaluation_report.json", help="Path to save report")
    args = parser.parse_args()

    try:
        # Load Data
        df = load_processed_data(args.input)
        
        # Train Model
        X = df[['mean_atomic_radius', 'electronegativity_variance', 
                'valence_electron_count', 'hume_rothery_concentration']].values
        y = df['temperature'].values
        
        # Handle NaNs
        valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[valid_mask]
        y = y[valid_mask]
        df_valid = df[valid_mask]

        model = train_random_forest(X, y)
        
        # Run LOSO
        loso_results = run_loso_cv(df_valid, model)
        
        # Perform Power Analysis
        success, power_report = perform_power_analysis(df_valid, loso_results)
        
        if not success:
            log_error("Power analysis failed. Halting pipeline.")
            # Write the report to the output file even if failed for transparency
            loso_results['power_analysis'] = power_report
            loso_results['status'] = 'FAILED_POWER_ANALYSIS'
            save_report(loso_results, args.output_report)
            sys.exit(1)
        
        # Save Model
        os.makedirs(os.path.dirname(args.output_model), exist_ok=True)
        save_model(model, args.output_model)
        
        # Save Report
        loso_results['power_analysis'] = power_report
        loso_results['status'] = 'SUCCESS'
        save_report(loso_results, args.output_report)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        log_error(f"Pipeline execution failed: {e}")
        raise

if __name__ == "__main__":
    main()
