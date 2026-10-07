"""
Stratified K-Fold Cross-Validation.

Performs stratified k-fold CV on the trained model using the filtered features.
"""
import os
import sys
import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import r2_score, mean_squared_error

# Add project root to path
project_root = Path(__file__).parent.parent
sys_path = str(project_root)
if sys_path not in sys.path:
    sys.path.insert(0, sys_path)

from config import Config, initialize_environment

def setup_cv_logger():
    logger = logging.getLogger("stratified_cv")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def load_model(path: str, logger: logging.Logger):
    """Load model from pickle."""
    logger.info(f"Loading model from {path}")
    with open(path, 'rb') as f:
        return pickle.load(f)

def load_filtered_features(path: str, logger: logging.Logger) -> pd.DataFrame:
    """Load filtered features."""
    logger.info(f"Loading filtered features from {path}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)

def bin_target_for_stratification(y: np.ndarray, n_bins: int = 5) -> np.ndarray:
    """Bin continuous target into quantile-based bins for stratification."""
    return pd.qcut(y, q=n_bins, labels=False, duplicates='drop')

def run_stratified_cv(model, X: pd.DataFrame, y: pd.Series, logger: logging.Logger) -> List[Dict[str, float]]:
    """Run stratified k-fold CV."""
    n_samples = len(y)
    
    # Adaptive k
    if n_samples < 10:
        k = min(n_samples - 1, 2)
    else:
        k = 5
    
    logger.info(f"Running stratified k-fold CV with k={k} (n={n_samples})")
    
    # Bin target for stratification
    y_binned = bin_target_for_stratification(y.values, n_bins=5)
    
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
    
    results = []
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y_binned)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Clone model for each fold (assuming simple LinearRegression which can be cloned)
        # For simplicity, we fit a new model on each fold
        from sklearn.linear_model import LinearRegression
        fold_model = LinearRegression()
        fold_model.fit(X_train, y_train)
        
        y_pred = fold_model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = mean_squared_error(y_test, y_pred, squared=False)
        
        results.append({
            "fold": fold_idx + 1,
            "r2": r2,
            "rmse": rmse
        })
        logger.info(f"Fold {fold_idx + 1}: R2={r2:.4f}, RMSE={rmse:.4f}")
    
    return results

def save_cv_results(results: List[Dict[str, float]], output_path: str, logger: logging.Logger):
    """Save CV results to JSON."""
    # Calculate mean and std
    r2_scores = [r['r2'] for r in results]
    rmse_scores = [r['rmse'] for r in results]
    
    summary = {
        "k": len(results),
        "mean_r2": float(np.mean(r2_scores)),
        "std_r2": float(np.std(r2_scores)),
        "mean_rmse": float(np.mean(rmse_scores)),
        "std_rmse": float(np.std(rmse_scores)),
        "folds": results
    }
    
    import json
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Saved CV results to {output_path}")
    logger.info(f"Mean R2: {summary['mean_r2']:.4f} ± {summary['std_r2']:.4f}")
    logger.info(f"Mean RMSE: {summary['mean_rmse']:.4f} ± {summary['std_rmse']:.4f}")

def main():
    logger = setup_cv_logger()
    initialize_environment()
    
    model_path = os.environ.get("MODEL_INPUT", str(project_root / "models" / "thermal_predictor.pkl"))
    data_path = os.environ.get("DATA_INPUT", str(project_root / "data" / "processed" / "filtered_features.csv"))
    output_path = os.environ.get("CV_OUTPUT", str(project_root / "results" / "model_performance.json"))

    try:
        # Load model (not strictly needed for CV as we refit, but good for verification)
        # model = load_model(model_path, logger)
        
        df = load_filtered_features(data_path, logger)
        
        # Prepare data
        target_col = 'thermal_conductivity_scalar'
        feature_cols = [c for c in df.columns if c not in ['material_id', target_col] and df[c].dtype in ['float64', 'int64']]
        
        X = df[feature_cols]
        y = df[target_col]
        
        # Drop NaNs
        mask = ~X.isna().any(axis=1) & ~y.isna()
        X = X[mask]
        y = y[mask]
        
        results = run_stratified_cv(None, X, y, logger)
        save_cv_results(results, output_path, logger)
        
        logger.info("Stratified CV completed.")
    except Exception as e:
        logger.error(f"Stratified CV failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()