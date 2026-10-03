import os
import sys
import logging
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
from typing import Dict, Any, List, Tuple

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config, initialize_environment
from utils import pin_seed

def setup_cv_logger() -> logging.Logger:
    """Setup logger for stratified CV task."""
    logger = logging.getLogger("stratified_cv_logger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_model(model_path: Path) -> Any:
    """Load the trained linear regression model."""
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info("Model loaded successfully")
    return model

def load_filtered_features(features_path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load filtered features and separate target.
    Expects 'thermal_conductivity_scalar' as the target column.
    """
    logger.info(f"Loading features from {features_path}")
    if not features_path.exists():
        raise FileNotFoundError(f"Filtered features file not found: {features_path}")
    
    df = pd.read_csv(features_path)
    
    # Verify target column exists
    target_col = 'thermal_conductivity_scalar'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in features file. Columns: {list(df.columns)}")
    
    # Drop rows with missing target or features
    initial_count = len(df)
    df = df.dropna(subset=[target_col])
    # Also drop rows where any feature is NaN
    feature_cols = [c for c in df.columns if c != target_col]
    df = df.dropna(subset=feature_cols)
    
    if len(df) < initial_count:
        logger.warning(f"Dropped {initial_count - len(df)} rows due to missing values.")
    
    if len(df) < 5:
        raise ValueError("Not enough samples after dropping NaNs to perform cross-validation.")
    
    X = df[feature_cols]
    y = df[target_col]
    
    logger.info(f"Loaded {len(df)} samples with {len(feature_cols)} features")
    return X, y

def bin_target_for_stratification(y: pd.Series, n_bins: int = 5) -> pd.Series:
    """
    Bin continuous target into quantiles to enable stratification.
    Uses quantile-based binning to ensure roughly equal distribution per fold.
    """
    logger.info(f"Binning target into {n_bins} quantile bins for stratification")
    
    # Use pd.qcut to create bins based on quantiles
    # labels=False returns integer codes 0..n_bins-1
    try:
        y_binned = pd.qcut(y, q=n_bins, labels=False, duplicates='drop')
    except ValueError as e:
        # If duplicates='drop' still fails (e.g., too few unique values), fallback to uniform bins
        logger.warning(f"Quantile binning failed: {e}. Falling back to uniform binning.")
        y_binned = pd.cut(y, bins=n_bins, labels=False)
    
    # Ensure we have at least 2 bins for stratification
    if len(np.unique(y_binned)) < 2:
        logger.warning("Only 1 unique bin found. Cannot stratify. Falling back to random shuffle (no stratification).")
        # Return None to indicate stratification is not possible
        return None
    
    logger.info(f"Created {len(np.unique(y_binned))} bins for stratification")
    return y_binned

def run_stratified_cv(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    k: int = 5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Perform stratified k-fold cross-validation.
    Returns a dictionary with fold results and aggregate stats.
    """
    logger.info(f"Starting {k}-fold stratified cross-validation with seed {seed}")
    pin_seed(seed)
    
    y_binned = bin_target_for_stratification(y, n_bins=k)
    
    results: List[Dict[str, float]] = []
    
    if y_binned is not None:
        skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
        fold_generator = skf.split(X, y_binned)
        logger.info("Using StratifiedKFold")
    else:
        # Fallback: simple KFold if stratification is not possible
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=k, shuffle=True, random_state=seed)
        fold_generator = kf.split(X)
        logger.info("Using standard KFold (stratification not possible)")
    
    for fold_idx, (train_idx, test_idx) in enumerate(fold_generator):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Clone the model to avoid state leakage between folds
        # Assuming the model has a `set_params` or we can just create a new one if it's simple
        # For LinearRegression, we can just clone by re-instantiating if needed, 
        # but sklearn's clone is safer. However, to keep it simple and dependency-light:
        # We will just refit the same type of model.
        # Since we loaded a specific model instance, we clone it.
        # If the model is a LinearRegression, we can do:
        from sklearn.base import clone
        fold_model = clone(model)
        
        fold_model.fit(X_train, y_train)
        
        y_pred = fold_model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        fold_result = {
            "fold": fold_idx + 1,
            "r2": float(r2),
            "rmse": float(rmse),
            "train_size": len(train_idx),
            "test_size": len(test_idx)
        }
        results.append(fold_result)
        logger.info(f"Fold {fold_idx + 1}: R² = {r2:.4f}, RMSE = {rmse:.4f}")
    
    # Aggregate results
    r2_scores = [r["r2"] for r in results]
    rmse_scores = [r["rmse"] for r in results]
    
    aggregate = {
        "k": k,
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "rmse_mean": float(np.mean(rmse_scores)),
        "rmse_std": float(np.std(rmse_scores)),
        "folds": results
    }
    
    return aggregate

def save_cv_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save CV results to JSON."""
    logger.info(f"Saving CV results to {output_path}")
    with open(output_path, 'w') as f:
        import json
        json.dump(results, f, indent=2)
    logger.info("Results saved successfully")

def main():
    """Main entry point for T023."""
    logger = setup_cv_logger()
    logger.info("Starting T023: Stratified K-Fold Cross-Validation")
    
    # Initialize config and seed
    initialize_environment()
    config = Config()
    seed = config.get("RANDOM_SEED", 42)
    
    # Define paths
    model_path = Path("models/thermal_predictor.pkl")
    features_path = Path("data/processed/filtered_features.csv")
    output_path = Path("results/model_performance.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load model
        model = load_model(model_path)
        
        # Load features
        X, y = load_filtered_features(features_path)
        
        # Run CV
        results = run_stratified_cv(model, X, y, k=5, seed=seed)
        
        # Save results
        save_cv_results(results, output_path)
        
        logger.info("T023 completed successfully.")
        return 0
    
    except Exception as e:
        logger.error(f"T023 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())