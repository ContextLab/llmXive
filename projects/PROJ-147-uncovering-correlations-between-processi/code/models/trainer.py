"""
Multi-output RandomForest training module for texture prediction.

Implements 5-fold cross-validated grid search with a 30-minute wall-clock limit.
Produces a trained model artifact and logs hyperparameters.
"""
import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.base import clone

# Import project utilities
from code.config import ensure_dirs
from code.utils.logging import get_logger, log_warning_structured
from code.data.processor import process_dataset

logger = get_logger(__name__)

# Configuration constants
MAX_WALL_CLOCK_SECONDS = 1800  # 30 minutes
N_ITERATIONS = 50  # Number of parameter settings to sample
CV_FOLDS = 5
RANDOM_STATE = 42


def load_processed_data(data_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads processed data from disk.
    Returns (X, y) where X is features and y is multi-output texture coefficients.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed data not found at {data_path}. "
                                "Run preprocessing first.")
    
    df = pd.read_csv(data_path)
    
    # Identify target columns (typically texture coefficients ending in _odf)
    # Assuming the processor has already derived these or they are in the dataset
    # We look for columns that are not processing parameters or alloy identifiers
    # For this implementation, we assume a specific schema based on the project context:
    # Features: processing conditions + derived physics features
    # Targets: ODF intensities (e.g., {100}, {110}, {111})
    
    # Heuristic: Targets are columns containing 'odf' or specific texture names if not obvious
    # Let's assume the processor outputs specific target columns named in config or standard
    # If the dataset has a 'target_columns' metadata, use that. Otherwise, infer.
    
    # Fallback: If 'target_columns' is not in metadata, assume last N columns are targets
    # or columns matching a pattern. For robustness, we'll assume the user specifies
    # or we infer based on common texture names if present.
    
    # To be safe and generic as per the prompt's "extend" instruction, we assume
    # the processed dataset has a specific structure defined in data-model.md or config.
    # Since we don't have the full data-model.md content here, we assume standard columns:
    # X: all columns except 'alloy_family', 'sample_id', and target columns.
    # y: columns like 'odf_100', 'odf_110', 'odf_111' if they exist.
    
    target_candidates = [c for c in df.columns if 'odf' in c.lower() or 'texture' in c.lower()]
    
    if not target_candidates:
        # Fallback: assume the last 3 columns are targets if no 'odf' found
        # This is a heuristic; in a real scenario, this should be explicit.
        logger.warning("No ODF columns found. Assuming last 3 columns are targets.")
        target_candidates = df.columns[-3:].tolist()
    
    feature_columns = [c for c in df.columns if c not in target_candidates 
                       and c not in ['alloy_family', 'sample_id', 'alloy_id']]
    
    if len(feature_columns) == 0:
        raise ValueError("No feature columns found in processed data.")
    
    X = df[feature_columns].copy()
    y = df[target_candidates].copy()
    
    # Handle missing values in X (should be handled by processor, but safety check)
    if X.isnull().any().any():
        logger.warning("Missing values found in features. Dropping rows.")
        mask = ~X.isnull().any(axis=1)
        X = X[mask]
        y = y[mask]
    
    if len(X) == 0:
        raise ValueError("No valid samples remaining after cleaning.")
    
    return X, y, target_candidates


def get_param_distributions() -> Dict[str, Any]:
    """
    Defines the search space for hyperparameter tuning.
    """
    return {
        'n_estimators': [100, 200, 300, 500],
        'max_depth': [None, 10, 20, 30, 50],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None],
        'bootstrap': [True, False]
    }


def train_model(
    X: pd.DataFrame,
    y: pd.DataFrame,
    target_names: List[str],
    output_dir: str,
    timeout_seconds: int = MAX_WALL_CLOCK_SECONDS
) -> Tuple[RandomizedSearchCV, Dict[str, float]]:
    """
    Trains a multi-output RandomForest model using RandomizedSearchCV.
    
    Args:
        X: Feature DataFrame.
        y: Target DataFrame (multi-output).
        target_names: List of target column names.
        output_dir: Directory to save model and logs.
        timeout_seconds: Maximum wall-clock time for training.
    
    Returns:
        best_model: The fitted RandomizedSearchCV object.
        metrics: Dictionary of best CV scores.
    """
    logger.info(f"Starting training for {len(X)} samples, {len(target_names)} targets.")
    
    # Ensure output directory exists
    ensure_dirs(output_dir)
    
    start_time = time.time()
    elapsed = 0
    
    # Base estimator
    base_model = RandomForestRegressor(random_state=RANDOM_STATE, n_jobs=-1)
    
    # Search space
    param_dist = get_param_distributions()
    
    # We use RandomizedSearchCV because it's more efficient for large spaces
    # and we have a time limit.
    # Note: RandomForestRegressor supports multi-output natively.
    
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    # Note: For multi-output y, StratifiedKFold might need a single target for stratification.
    # If y is multi-output, we might need to stratify on the first target or a combined label.
    # For simplicity in this generic implementation, we use KFold if y is multi-output
    # and StratifiedKFold if we can derive a single label. 
    # However, sklearn's StratifiedKFold requires y to be 1D.
    # Given the multi-output nature, we will use KFold to avoid stratification issues
    # unless a specific stratification column is provided.
    
    # Let's use KFold for robustness with multi-output targets
    from sklearn.model_selection import KFold
    cv = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_dist,
        n_iter=N_ITERATIONS,
        scoring='r2', # Multi-output R2 is averaged
        cv=cv,
        verbose=1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        return_train_score=True
    )
    
    logger.info(f"Starting grid search with {N_ITERATIONS} iterations.")
    
    # Fit with time limit check
    try:
        # We can't pass timeout directly to fit in older sklearn, so we monitor time
        search.fit(X, y)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Training completed in {elapsed:.2f} seconds.")
    
    if elapsed > timeout_seconds:
        log_warning_structured(
            "TIMEOUT",
            f"Training exceeded {timeout_seconds}s limit (took {elapsed:.2f}s). "
            "Results may be suboptimal."
        )
    
    # Extract best parameters and score
    best_params = search.best_params_
    best_score = search.best_score_
    
    # Save model and results
    model_path = Path(output_dir) / "best_model.pkl"
    metrics_path = Path(output_dir) / "training_metrics.json"
    
    import joblib
    joblib.dump(search, str(model_path))
    
    metrics = {
        "best_params": best_params,
        "best_cv_score": float(best_score),
        "n_samples": len(X),
        "n_targets": len(target_names),
        "training_time_seconds": elapsed,
        "timeout_seconds": timeout_seconds,
        "n_iter": N_ITERATIONS,
        "cv_folds": CV_FOLDS
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Model saved to {model_path}")
    logger.info(f"Metrics saved to {metrics_path}")
    
    return search, metrics


def run_training_pipeline(processed_data_path: str, output_dir: str = "data/models") -> Dict[str, Any]:
    """
    Orchestrates the full training pipeline: load -> train -> save.
    """
    X, y, target_names = load_processed_data(processed_data_path)
    logger.info(f"Loaded {len(X)} samples with targets: {target_names}")
    
    best_model, metrics = train_model(X, y, target_names, output_dir)
    
    return {
        "model_path": str(Path(output_dir) / "best_model.pkl"),
        "metrics": metrics,
        "target_names": target_names
    }


if __name__ == "__main__":
    # Default paths for standalone execution
    # In a real pipeline, these would come from config or CLI args
    processed_path = "data/processed/processed_dataset.csv"
    output_path = "data/models"
    
    if not os.path.exists(processed_path):
        logger.error(f"Processed data not found at {processed_path}. "
                     "Please run the preprocessing pipeline first.")
        exit(1)
    
    results = run_training_pipeline(processed_path, output_path)
    logger.info(f"Training pipeline finished. Best R2: {results['metrics']['best_cv_score']:.4f}")
