import os
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold, RepeatedKFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor
from pygam import LinearGAM, s
import joblib
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import existing utilities from config to ensure paths/seeds are consistent
import sys
# Ensure the code directory is in the path for imports if run as script
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.utils.config import PROJECT_ROOT, RANDOM_SEED, THRESHOLDS
except ImportError:
    # Fallback if config is not fully implemented yet, though T004 should exist
    logger.warning("Could not import config. Using defaults.")
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    RANDOM_SEED = 42
    THRESHOLDS = {'low': 0.01, 'medium': 0.05, 'high': 0.10}

def train_gam(X: np.ndarray, y: np.ndarray, n_folds: int = 3) -> Dict[str, Any]:
    """
    Train a Generalized Additive Model (GAM) with splines.
    Uses 3-fold CV by default; if dataset size < 100, switches to 10-Fold Repeated CV.
    """
    n_samples = X.shape[0]
    logger.info(f"Training GAM on {n_samples} samples.")

    # Determine CV strategy based on dataset size
    if n_samples < 100:
        logger.info("Dataset size < 100. Switching to 10-Fold Repeated CV.")
        cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=RANDOM_SEED)
        folds_used = "10-Fold Repeated"
    else:
        logger.info(f"Dataset size >= 100. Using {n_folds}-Fold CV.")
        cv = KFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
        folds_used = f"{n_folds}-Fold"

    # Initialize GAM
    # Using natural splines (s) for all features. 
    # Note: In a real scenario, we might select specific features for splines vs linear.
    # Here we apply splines to all numeric features for the sake of the implementation.
    n_features = X.shape[1]
    terms = [s(i) for i in range(n_features)]
    model = LinearGAM(*terms, random_state=RANDOM_SEED)

    # Cross-validation scores
    try:
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        mean_r2 = np.mean(scores)
        std_r2 = np.std(scores)
    except Exception as e:
        logger.error(f"Cross-validation failed for GAM: {e}")
        mean_r2 = np.nan
        std_r2 = np.nan

    # Fit on full data
    model.fit(X, y)

    return {
        "model": model,
        "model_type": "GAM",
        "cv_strategy": folds_used,
        "r2_mean": mean_r2,
        "r2_std": std_r2,
        "n_samples": n_samples
    }

def train_regularized_linear(X: np.ndarray, y: np.ndarray, n_folds: int = 3) -> Dict[str, Any]:
    """
    Train a Regularized Linear Regression (Ridge) model.
    Uses 3-fold CV by default; if dataset size < 100, switches to 10-Fold Repeated CV.
    """
    n_samples = X.shape[0]
    logger.info(f"Training Regularized Linear Regression on {n_samples} samples.")

    # Determine CV strategy
    if n_samples < 100:
        logger.info("Dataset size < 100. Switching to 10-Fold Repeated CV.")
        cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=RANDOM_SEED)
        folds_used = "10-Fold Repeated"
    else:
        logger.info(f"Dataset size >= 100. Using {n_folds}-Fold CV.")
        cv = KFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
        folds_used = f"{n_folds}-Fold"

    model = Ridge(random_state=RANDOM_SEED)

    try:
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        mean_r2 = np.mean(scores)
        std_r2 = np.std(scores)
    except Exception as e:
        logger.error(f"Cross-validation failed for Ridge: {e}")
        mean_r2 = np.nan
        std_r2 = np.nan

    model.fit(X, y)

    return {
        "model": model,
        "model_type": "RegularizedLinear",
        "cv_strategy": folds_used,
        "r2_mean": mean_r2,
        "r2_std": std_r2,
        "n_samples": n_samples
    }

def train_random_forest(X: np.ndarray, y: np.ndarray, n_folds: int = 3) -> Dict[str, Any]:
    """
    Train a Random Forest Regressor.
    Uses 3-fold CV by default; if dataset size < 100, switches to 10-Fold Repeated CV.
    CPU-only, no CUDA.
    """
    n_samples = X.shape[0]
    logger.info(f"Training Random Forest on {n_samples} samples.")

    # Determine CV strategy
    if n_samples < 100:
        logger.info("Dataset size < 100. Switching to 10-Fold Repeated CV.")
        cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=RANDOM_SEED)
        folds_used = "10-Fold Repeated"
    else:
        logger.info(f"Dataset size >= 100. Using {n_folds}-Fold CV.")
        cv = KFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
        folds_used = f"{n_folds}-Fold"

    # Initialize RF with CPU-only settings
    # n_jobs=-1 uses all available CPU cores, but no CUDA/GPU
    model = RandomForestRegressor(
        n_estimators=100, 
        max_depth=None, 
        random_state=RANDOM_SEED, 
        n_jobs=-1, 
        verbose=0
    )

    try:
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        mean_r2 = np.mean(scores)
        std_r2 = np.std(scores)
    except Exception as e:
        logger.error(f"Cross-validation failed for Random Forest: {e}")
        mean_r2 = np.nan
        std_r2 = np.nan

    model.fit(X, y)

    return {
        "model": model,
        "model_type": "RandomForest",
        "cv_strategy": folds_used,
        "r2_mean": mean_r2,
        "r2_std": std_r2,
        "n_samples": n_samples
    }

def train_xgboost(X: np.ndarray, y: np.ndarray, n_folds: int = 3) -> Dict[str, Any]:
    """
    Train an XGBoost Regressor.
    Uses 3-fold CV by default; if dataset size < 100, switches to 10-Fold Repeated CV.
    CPU-only, no CUDA.
    """
    n_samples = X.shape[0]
    logger.info(f"Training XGBoost on {n_samples} samples.")

    # Determine CV strategy
    if n_samples < 100:
        logger.info("Dataset size < 100. Switching to 10-Fold Repeated CV.")
        cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=RANDOM_SEED)
        folds_used = "10-Fold Repeated"
    else:
        logger.info(f"Dataset size >= 100. Using {n_folds}-Fold CV.")
        cv = KFold(n_splits=n_folds, shuffle=True, random_state=RANDOM_SEED)
        folds_used = f"{n_folds}-Fold"

    # Initialize XGB with CPU-only settings
    # tree_method='hist' is efficient for CPU
    model = XGBRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        random_state=RANDOM_SEED,
        tree_method='hist', # CPU efficient
        n_jobs=-1,
        verbosity=0
    )

    try:
        scores = cross_val_score(model, X, y, cv=cv, scoring='r2')
        mean_r2 = np.mean(scores)
        std_r2 = np.std(scores)
    except Exception as e:
        logger.error(f"Cross-validation failed for XGBoost: {e}")
        mean_r2 = np.nan
        std_r2 = np.nan

    model.fit(X, y)

    return {
        "model": model,
        "model_type": "XGBoost",
        "cv_strategy": folds_used,
        "r2_mean": mean_r2,
        "r2_std": std_r2,
        "n_samples": n_samples
    }

def run_training_pipeline(data_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Runs the full training pipeline for all model types (GAM, Linear, RF, XGBoost).
    Loads data from data_path, trains models, saves artifacts to output_dir.
    
    Args:
        data_path: Path to the processed CSV file (e.g., data/processed/cleaned_data.csv)
        output_dir: Directory to save model artifacts (e.g., data/results/models)
    
    Returns:
        Dictionary containing results summary for all models.
    """
    logger.info(f"Starting training pipeline. Loading data from {data_path}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded data: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to load data from {data_path}: {e}")
        return {"error": str(e)}

    # Identify target and features
    # Assuming the target column is named 'yield_strength' based on domain context
    target_col = 'yield_strength'
    if target_col not in df.columns:
        # Fallback: try to find a column that looks like yield strength
        candidates = [c for c in df.columns if 'yield' in c.lower() or 'strength' in c.lower()]
        if candidates:
            target_col = candidates[0]
            logger.warning(f"Target column '{target_col}' not found. Using '{target_col}'.")
        else:
            logger.error(f"Could not identify target column. Columns: {df.columns.tolist()}")
            return {"error": "Target column not found"}

    X = df.drop(columns=[target_col]).select_dtypes(include=[np.number]).values
    y = df[target_col].values

    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        logger.warning("NaN values detected in data. Dropping rows with NaN.")
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        logger.info(f"Remaining data shape after NaN removal: {X.shape}")

    if X.shape[0] == 0:
        logger.error("No valid data remaining after cleaning.")
        return {"error": "No valid data"}

    results = {}

    # Train GAM
    logger.info("Training GAM...")
    results['gam'] = train_gam(X, y)
    joblib.dump(results['gam']['model'], os.path.join(output_dir, 'model_gam.joblib'))

    # Train Regularized Linear
    logger.info("Training Regularized Linear...")
    results['linear'] = train_regularized_linear(X, y)
    joblib.dump(results['linear']['model'], os.path.join(output_dir, 'model_linear.joblib'))

    # Train Random Forest (T020 requirement)
    logger.info("Training Random Forest...")
    results['rf'] = train_random_forest(X, y)
    joblib.dump(results['rf']['model'], os.path.join(output_dir, 'model_rf.joblib'))

    # Train XGBoost (T020 requirement)
    logger.info("Training XGBoost...")
    results['xgb'] = train_xgboost(X, y)
    joblib.dump(results['xgb']['model'], os.path.join(output_dir, 'model_xgb.joblib'))

    # Save summary
    summary = {k: {
        'type': v['model_type'],
        'cv_strategy': v['cv_strategy'],
        'r2_mean': v['r2_mean'],
        'r2_std': v['r2_std'],
        'n_samples': v['n_samples']
    } for k, v in results.items()}

    summary_path = os.path.join(output_dir, 'training_summary.json')
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Training pipeline complete. Summary saved to {summary_path}")
    return results

if __name__ == "__main__":
    # Example execution for testing
    # In a real run, paths would be passed via CLI or config
    sample_data_path = os.path.join(PROJECT_ROOT, "data", "processed", "cleaned_data.csv")
    output_directory = os.path.join(PROJECT_ROOT, "data", "results", "models")
    
    if os.path.exists(sample_data_path):
        run_training_pipeline(sample_data_path, output_directory)
    else:
        logger.info(f"Sample data not found at {sample_data_path}. Skipping execution.")
        logger.info("To run, ensure data/processed/cleaned_data.csv exists.")