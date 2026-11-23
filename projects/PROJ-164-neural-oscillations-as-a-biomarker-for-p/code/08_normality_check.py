import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy.stats import shapiro
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import Ridge
from scipy.stats import rankdata

# Import project utilities
from utils.config import PROJECT_ID, DATA_PROCESSED, MODELS, LOGS
from utils.logging_setup import get_logger, log_mode_switch
from utils.io_helpers import load_json, write_json

# Ensure paths exist
LOGS_PATH = Path(LOGS)
LOGS_PATH.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

# Constants
ALPHA = 0.05
MODEL_TYPE_NORMAL = "Ridge"
MODEL_TYPE_NON_NORMAL = "Rank-Ridge"

def load_feature_matrix() -> pd.DataFrame:
    """
    Load the feature matrix produced by T025.
    Expected path: data/processed/feature_matrix.csv
    """
    input_path = Path(DATA_PROCESSED) / "feature_matrix.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {input_path}. "
                                "Please ensure T025 has completed successfully.")
    
    df = pd.read_csv(input_path)
    
    # Identify the target column (tDCS response)
    # Based on spec, the target is usually named 'response', 'target', or 'tdcs_response'
    # We look for a column that is numeric and not a subject ID
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Heuristic: The last numeric column is often the target in these pipelines,
    # or explicitly named. Let's look for 'response' or similar.
    target_candidates = [c for c in numeric_cols if 'response' in c.lower() or 'target' in c.lower()]
    
    if not target_candidates:
        # Fallback: assume the last column is the target if it's not subject_id
        # This is risky but necessary if naming is inconsistent.
        # A better approach relies on the schema from T007.
        # Assuming schema: subject_id, ..., response
        if 'subject_id' in df.columns:
            target_col = [c for c in numeric_cols if c != 'subject_id'][-1]
        else:
            target_col = numeric_cols[-1]
        logger.warning(f"Could not auto-detect target column. Using '{target_col}'.")
    else:
        target_col = target_candidates[0]
    
    logger.info(f"Target column identified as: {target_col}")
    return df, target_col

def perform_normality_test(target_series: pd.Series) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test on the target variable.
    Returns dictionary with statistic, p-value, and normality decision.
    """
    # Clean data: remove NaNs
    clean_data = target_series.dropna()
    
    if len(clean_data) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test (< 3). "
                       "Assuming non-normal and switching to Rank-Ridge.")
        return {
            "statistic": None,
            "p_value": None,
            "is_normal": False,
            "reason": "Sample size too small"
        }

    stat, p_val = shapiro(clean_data)
    is_normal = p_val >= ALPHA

    logger.info(f"Shapiro-Wilk Test: statistic={stat:.4f}, p-value={p_val:.4f}")
    logger.info(f"Normality Decision: {'Normal' if is_normal else 'Non-Normal'} (alpha={ALPHA})")

    return {
        "statistic": float(stat),
        "p_value": float(p_val),
        "is_normal": is_normal,
        "alpha": ALPHA,
        "sample_size": len(clean_data)
    }

def fit_rank_ridge(X: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> Ridge:
    """
    Fit a Rank-Ridge regression model.
    Steps:
    1. Rank transform the target variable y.
    2. Fit a standard Ridge regression on the ranked target.
    """
    # Rank transform y
    # rankdata returns ranks from 1 to n. We can use these directly or normalize.
    # Standard practice: use ranks as the new target.
    y_ranks = rankdata(y)
    
    # Normalize ranks to [0, 1] to keep scale similar to original if needed,
    # but Ridge is scale-invariant regarding the target's mean/variance mostly,
    # though alpha regularization depends on scale.
    # Let's keep raw ranks for simplicity as Ridge minimizes squared error.
    
    model = Ridge(alpha=alpha)
    model.fit(X, y_ranks)
    
    # Store original y mean/std for potential inverse transform if needed later,
    # though for prediction we usually predict ranks and compare rank correlation.
    model._original_y = y
    model._rank_transform = True
    
    return model

def run_model_selection_and_fitting(X: np.ndarray, y: np.ndarray, is_normal: bool) -> Dict[str, Any]:
    """
    Run nested CV or simple fitting based on normality.
    For T028, we primarily need to determine the model type and perform the fit.
    T026 will handle the full nested CV. Here we do a preliminary fit to confirm viability.
    """
    model_type = MODEL_TYPE_NORMAL if is_normal else MODEL_TYPE_NON_NORMAL
    logger.info(f"Selected Model Type: {model_type}")
    
    # Simple train/test split for immediate verification (not full CV yet)
    # Or just fit on all if N is small, but let's do a simple split to avoid overfitting in this step
    n_samples = X.shape[0]
    if n_samples < 10:
        logger.warning("Small sample size. Fitting on full data for demonstration.")
        X_train, y_train = X, y
    else:
        split_idx = int(0.8 * n_samples)
        X_train, y_train = X[:split_idx], y[:split_idx]
    
    if is_normal:
        model = Ridge(alpha=1.0) # Default alpha, T026 will optimize
        model.fit(X_train, y_train)
    else:
        model = fit_rank_ridge(X_train, y_train, alpha=1.0)
    
    # Save the preliminary model
    model_path = Path(MODELS)
    model_path.mkdir(parents=True, exist_ok=True)
    
    if is_normal:
        output_path = model_path / "ridge_model.pkl"
    else:
        output_path = model_path / "rank_ridge_model.pkl"
    
    import pickle
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved to {output_path}")
    
    return {
        "model_type": model_type,
        "model_path": str(output_path),
        "is_normal": is_normal
    }

def main():
    logger.info("Starting Normality Check (T028)...")
    
    try:
        # 1. Load Data
        df, target_col = load_feature_matrix()
        y = df[target_col].values
        
        # 2. Extract Features (exclude target and ID)
        feature_cols = [c for c in df.columns if c != target_col and c != 'subject_id']
        if not feature_cols:
            raise ValueError("No feature columns found in feature_matrix.csv")
        
        X = df[feature_cols].values
        
        # 3. Perform Normality Test
        normality_result = perform_normality_test(df[target_col])
        
        # 4. Determine Model Strategy
        is_normal = normality_result['is_normal']
        
        # 5. Fit Preliminary Model
        fitting_result = run_model_selection_and_fitting(X, y, is_normal)
        
        # 6. Write Results
        output_path = Path(DATA_PROCESSED) / "normality_check_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "task_id": "T028",
            "normality_test": normality_result,
            "model_decision": fitting_result,
            "next_step": "Proceed to T026 (Nested CV) using the selected model type."
        }
        
        write_json(output_path, report)
        logger.info(f"Results written to {output_path}")
        
        # Log mode switch if necessary (though T027 handles the main gate, T028 triggers the logic switch)
        if not is_normal:
            log_mode_switch(logger, "Switching to Rank-Ridge regression due to non-normal target distribution.")
        
        logger.info("T028 completed successfully.")
        
    except Exception as e:
        logger.error(f"T028 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
