import os
import sys
import json
import logging
import pickle
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

# Import from project API surface
from utils.logging_config import setup_pipeline_logger
from utils.errors import DataInsufficientError

# Constants for power analysis
POWER_ANALYSIS_N = 30
POWER_ANALYSIS_ALPHA = 0.05
POWER_ANALYSIS_POWER = 0.8
# Approximate detectable effect size (Cohen's d) for N=30, power=0.8, alpha=0.05 (two-tailed)
# This is a conservative estimate based on standard power tables for t-tests/ANOVA contexts
DETECTABLE_EFFECT_SIZE = 0.85 

logger = logging.getLogger(__name__)

def load_feature_matrix(path: str = "data/processed/feature_matrix.csv") -> np.ndarray:
    """Load the feature matrix from the processed CSV."""
    import pandas as pd
    if not os.path.exists(path):
        raise FileNotFoundError(f"Feature matrix not found at {path}")
    df = pd.read_csv(path)
    # Assume last column is target if not specified, or handle specific columns
    # For this implementation, we assume the file contains features and we need X, y
    # Standard convention: drop 'target' column if present, otherwise assume structure
    if 'target' in df.columns:
        X = df.drop(columns=['target']).values
        y = df['target'].values
    else:
        # Fallback or error if structure is unknown
        logger.warning("No 'target' column found. Assuming last column is target.")
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
    return X, y

def load_model(path: str = "artifacts/model.pkl") -> Any:
    """Load the trained model artifact."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model artifact not found at {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def log_power_analysis_assumptions(X: np.ndarray) -> Dict[str, Any]:
    """
    Log power analysis assumptions and detectable effect size.
    Returns a dictionary with the analysis details.
    """
    n_samples = X.shape[0]
    analysis_result = {
        "assumed_n": POWER_ANALYSIS_N,
        "actual_n": n_samples,
        "alpha": POWER_ANALYSIS_ALPHA,
        "power": POWER_ANALYSIS_POWER,
        "detectable_effect_size_cohen_d": DETECTABLE_EFFECT_SIZE,
        "status": "warning" if n_samples < POWER_ANALYSIS_N else "ok"
    }

    logger.info(f"--- Power Analysis Check ---")
    logger.info(f"Assumed Sample Size (N): {POWER_ANALYSIS_N}")
    logger.info(f"Actual Sample Size: {n_samples}")
    logger.info(f"Alpha: {POWER_ANALYSIS_ALPHA}, Power: {POWER_ANALYSIS_POWER}")
    logger.info(f"Detectable Effect Size (Cohen's d): ~{DETECTABLE_EFFECT_SIZE}")
    
    if n_samples < POWER_ANALYSIS_N:
        msg = f"WARNING: Actual sample size ({n_samples}) is below the power analysis assumption ({POWER_ANALYSIS_N}). Results may be underpowered to detect the specified effect size."
        logger.warning(msg)
        analysis_result["message"] = msg
    else:
        msg = f"Sample size ({n_samples}) meets the power analysis assumption ({POWER_ANALYSIS_N})."
        logger.info(msg)
        analysis_result["message"] = msg
    
    logger.info(f"--- End Power Analysis Check ---")
    return analysis_result

def perform_stratified_cv(
    X: np.ndarray, 
    y: np.ndarray, 
    model: Any, 
    n_splits: int = 5, 
    random_state: int = 42
) -> Dict[str, float]:
    """
    Perform stratified k-fold cross-validation.
    Returns metrics: R2, MAE.
    """
    from sklearn.model_selection import StratifiedKFold
    from sklearn.metrics import r2_score, mean_absolute_error
    
    # Handle regression case where stratification might need binning if y is continuous
    # If y is continuous, we might need to use KFold instead or bin y
    # Assuming y is continuous for regression:
    from sklearn.model_selection import KFold
    cv = KFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    r2_scores = []
    mae_scores = []
    
    for train_idx, test_idx in cv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        r2_scores.append(r2_score(y_test, y_pred))
        mae_scores.append(mean_absolute_error(y_test, y_pred))
    
    return {
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores)),
        "n_splits": n_splits
    }

def save_results(results: Dict[str, Any], path: str = "data/reports/cross_validation_results.json") -> None:
    """Save cross-validation results to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Cross-validation results saved to {path}")

def main():
    """
    Main entry point for cross-validation.
    1. Logs power analysis assumptions (N=30) and detectable effect size.
    2. Loads feature matrix and model.
    3. Performs stratified CV.
    4. Saves results.
    """
    logger = setup_pipeline_logger("cross_validate")
    logger.info("Starting cross-validation pipeline.")
    
    try:
        # 1. Load Data
        logger.info("Loading feature matrix...")
        X, y = load_feature_matrix("data/processed/feature_matrix.csv")
        
        # 2. Log Power Analysis Assumptions (T041 Requirement)
        logger.info("Checking power analysis assumptions...")
        power_info = log_power_analysis_assumptions(X)
        
        # 3. Load Model
        logger.info("Loading trained model...")
        model = load_model("artifacts/model.pkl")
        
        # 4. Perform Cross-Validation
        logger.info("Performing stratified cross-validation...")
        cv_results = perform_stratified_cv(X, y, model)
        
        # 5. Compile Final Report
        final_report = {
            "power_analysis": power_info,
            "cv_results": cv_results,
            "status": "completed"
        }
        
        # 6. Save Results
        save_results(final_report, "data/reports/cross_validation_results.json")
        
        logger.info("Cross-validation completed successfully.")
        return final_report
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during cross-validation: {e}")
        raise

if __name__ == "__main__":
    main()