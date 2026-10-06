import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from scipy import stats
import xarray as xr

from utils.logging_config import get_logger, setup_logging
from utils.config import get_config

# Ensure dependencies are available
try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except ImportError:
    raise ImportError("statsmodels is required for VIF calculation. Install via: pip install statsmodels")

logger = get_logger(__name__)
config = get_config()

def load_model_artifacts() -> Dict[str, Any]:
    """Load trained model artifacts (RF and optionally VLM)."""
    model_path = Path("data/artifacts/model_comparison.csv")
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifacts not found at {model_path}")
    
    # For this task, we primarily need the RF model for permutation importance.
    # We assume the RF model was saved during T018/T019 in a pickle or similar.
    # Since the specific pickle path isn't defined in the provided API, we infer it.
    rf_model_path = Path("data/artifacts/random_forest_model.pkl")
    
    if rf_model_path.exists():
        import pickle
        with open(rf_model_path, 'rb') as f:
            rf_model = pickle.load(f)
    else:
        # Fallback if T018 didn't save it explicitly but we need to proceed
        # In a real scenario, we would re-train or fail loudly.
        # We will assume the model exists as per T018 completion.
        raise FileNotFoundError(f"Random Forest model artifact not found at {rf_model_path}. T018 must complete successfully.")
    
    return {"rf_model": rf_model, "model_metrics_path": model_path}

def load_aligned_data(path: str = "data/processed/aligned_dataset.nc") -> xr.Dataset:
    """Load the aligned dataset created in T017."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Aligned data not found at {path}")
    ds = xr.open_dataset(p)
    return ds

def calculate_variance_inflation_factor(features: np.ndarray) -> np.ndarray:
    """
    Calculate Variance Inflation Factor (VIF) for each feature.
    VIF > 5 indicates potential multicollinearity.
    """
    if features.shape[0] < features.shape[1]:
        logger.warning("Sample size too small for reliable VIF calculation.")
        return np.ones(features.shape[1]) * np.nan
    
    vif_data = []
    for i in range(features.shape[1]):
        # Create a dataframe for the regression
        X = pd.DataFrame(features)
        y = X.iloc[:, i]
        X_regressors = X.drop(columns=[i])
        
        # Handle constant features or collinearity within regressors
        if X_regressors.empty:
            vif_data.append(np.nan)
            continue
        
        try:
            model = LinearRegression()
            model.fit(X_regressors, y)
            r_squared = model.score(X_regressors, y)
            vif = 1 / (1 - r_squared)
            vif_data.append(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for feature {i}: {e}")
            vif_data.append(np.nan)
    
    return np.array(vif_data)

def run_permutation_importance_analysis(
    model: Any, 
    X: np.ndarray, 
    y: np.ndarray, 
    feature_names: List[str],
    n_repeats: int = 10,
    random_state: int = 42,
    scoring: str = 'r2'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform permutation importance analysis.
    1. Calculate raw importance scores.
    2. Normalize scores to sum=1.0 using L1 norm.
    3. Verify sum equals unity within tolerance.
    4. Check for multicollinearity (VIF > 5) and log warnings.
    5. Write verification result to data/logs/importance_verification.log.
    """
    logger.info("Starting permutation importance analysis...")
    
    # 1. Check Multicollinearity (VIF)
    vif_scores = calculate_variance_inflation_factor(X)
    high_vif_indices = np.where(vif_scores > 5)[0]
    
    vif_warnings = []
    for idx in high_vif_indices:
        if idx < len(feature_names):
            vif_warnings.append(f"Feature '{feature_names[idx]}' has VIF > 5 ({vif_scores[idx]:.2f}). Proceeding without PCA as per spec.")
    
    if vif_warnings:
        for w in vif_warnings:
            logger.warning(w)
    
    # 2. Calculate Permutation Importance
    # Use the model's predict method. If model is RF, it has .score for R2.
    # permutation_importance returns mean and std of the score decrease.
    result = permutation_importance(
        model, X, y, 
        n_repeats=n_repeats, 
        random_state=random_state, 
        scoring=scoring,
        n_jobs=1 # Force single thread for determinism in this context
    )
    
    importance_scores = result.importances_mean
    
    # 3. Normalize scores to sum=1.0 (L1 Norm)
    # We take absolute values because importance can be negative (though usually positive for R2 decrease)
    # However, for "contribution", we want positive magnitudes.
    abs_importance = np.abs(importance_scores)
    total_sum = np.sum(abs_importance)
    
    if total_sum == 0:
        logger.warning("Total importance sum is zero. Cannot normalize.")
        normalized_scores = np.zeros_like(abs_importance)
    else:
        normalized_scores = abs_importance / total_sum
    
    # 4. Verify Sum equals unity
    tolerance = 1e-6
    sum_check = np.sum(normalized_scores)
    is_valid = np.isclose(sum_check, 1.0, atol=tolerance)
    
    verification_log = {
        "task_id": "T023",
        "total_raw_importance": float(np.sum(abs_importance)),
        "normalized_sum": float(sum_check),
        "tolerance": tolerance,
        "is_valid": is_valid,
        "vif_warnings": vif_warnings,
        "high_vif_features": [feature_names[i] for i in high_vif_indices if i < len(feature_names)],
        "feature_importance": {name: float(score) for name, score in zip(feature_names, normalized_scores)}
    }
    
    # 5. Write verification result to log
    log_path = Path("data/logs/importance_verification.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write(f"Permutation Importance Verification Report\n")
        f.write(f"{'='*50}\n")
        f.write(f"Timestamp: {pd.Timestamp.now().isoformat()}\n")
        f.write(f"Normalized Sum: {sum_check:.10f}\n")
        f.write(f"Target: 1.0\n")
        f.write(f"Tolerance: {tolerance}\n")
        f.write(f"Verification Status: {'PASSED' if is_valid else 'FAILED'}\n")
        f.write(f"\nMulticollinearity Check (VIF > 5):\n")
        if not vif_warnings:
            f.write("No features with VIF > 5 detected.\n")
        else:
            for w in vif_warnings:
                f.write(f"  - {w}\n")
        f.write(f"\nFeature Rankings (Normalized):\n")
        sorted_indices = np.argsort(normalized_scores)[::-1]
        for idx in sorted_indices:
            if idx < len(feature_names):
                f.write(f"  {feature_names[idx]}: {normalized_scores[idx]:.6f}\n")
    
    logger.info(f"Verification log written to {log_path}")
    
    # Create DataFrame for output
    df_importance = pd.DataFrame({
        "feature": feature_names,
        "raw_importance": importance_scores,
        "normalized_importance": normalized_scores
    }).sort_values(by="normalized_importance", ascending=False)
    
    return df_importance, verification_log

def main():
    """
    Main entry point for T023: Permutation Importance Analysis.
    Depends on T018 (RF Model) and T017 (Aligned Data).
    """
    setup_logging()
    
    try:
        # 1. Load Model
        artifacts = load_model_artifacts()
        rf_model = artifacts["rf_model"]
        logger.info("Loaded Random Forest model.")
        
        # 2. Load Data
        ds = load_aligned_data()
        logger.info("Loaded aligned dataset.")
        
        # Prepare X and y
        # Assume the dataset has a 'chlorophyll_a' or similar target variable, 
        # and other columns are features.
        # Based on T009a schema: temp, salinity, nutrients, chlorophyll_a.
        # Target is likely chlorophyll_a.
        
        target_col = "chlorophyll_a"
        if target_col not in ds.data_vars:
            # Fallback to common naming if different
            candidates = [c for c in ds.data_vars if 'chl' in c.lower() or 'chlorophyll' in c.lower()]
            if candidates:
                target_col = candidates[0]
            else:
                raise ValueError(f"Target column '{target_col}' not found in dataset.")
        
        # Select features (excluding target and non-numeric/coord vars)
        coords = list(ds.coords)
        features = [c for c in ds.data_vars if c != target_col and c not in coords]
        
        # Extract numpy arrays
        # Flatten spatial dimensions if present
        data_dict = {k: ds[k].values for k in features + [target_col]}
        
        # Handle NaNs
        df_raw = pd.DataFrame(data_dict)
        df_clean = df_raw.dropna()
        
        if len(df_clean) == 0:
            raise ValueError("No valid data points after dropping NaNs.")
        
        X = df_clean[features].values
        y = df_clean[target_col].values
        
        logger.info(f"Prepared X shape: {X.shape}, y shape: {y.shape}")
        
        # 3. Run Analysis
        df_importance, log_data = run_permutation_importance_analysis(
            model=rf_model,
            X=X,
            y=y,
            feature_names=features,
            n_repeats=10
        )
        
        # 4. Save Results
        output_path = Path("data/artifacts/feature_importance.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_importance.to_csv(output_path, index=False)
        logger.info(f"Saved feature importance to {output_path}")
        
        # Also save the verification JSON for programmatic access
        json_path = Path("data/artifacts/importance_verification.json")
        with open(json_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info("T023 completed successfully.")
        
    except Exception as e:
        logger.error(f"T023 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()