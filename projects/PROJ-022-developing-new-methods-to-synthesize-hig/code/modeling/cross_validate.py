"""
Cross-validation module for evaluating the trained membrane performance model.

This module implements stratified k-fold cross-validation to estimate the model's
generalization performance on unseen polymer data. It reports R² and MAE metrics
across folds.
"""
import os
import sys
import json
import logging
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime

from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.metrics import r2_score, mean_absolute_error, make_scorer
from sklearn.preprocessing import LabelEncoder

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, setup_pipeline_logger
from utils.errors import DataInsufficientError

logger = get_logger(__name__)

# Constants
DEFAULT_N_FOLDS = 5
RANDOM_SEED = 42
OUTPUT_DIR = project_root / "data" / "reports"
MODEL_PATH = project_root / "artifacts" / "model.pkl"
FEATURE_MATRIX_PATH = project_root / "data" / "processed" / "feature_matrix.csv"
CROSS_VAL_RESULTS_PATH = OUTPUT_DIR / "cross_validation_results.json"


def load_feature_matrix(path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load the feature matrix and target variable.
    
    Args:
        path: Path to the feature matrix CSV.
        
    Returns:
        Tuple of (X, y) where X is the feature dataframe and y is the target series.
        
    Raises:
        DataInsufficientError: If the file doesn't exist or is empty.
    """
    if not path.exists():
        raise DataInsufficientError(f"Feature matrix not found at {path}")
    
    df = pd.read_csv(path)
    
    # Expected columns based on previous pipeline steps
    # Target column is typically 'permeability_barrer' or similar
    target_col = 'permeability_barrer'
    
    if target_col not in df.columns:
        available_cols = list(df.columns)
        raise DataInsufficientError(
            f"Target column '{target_col}' not found in feature matrix. "
            f"Available columns: {available_cols}"
        )
    
    # Identify feature columns (exclude target and metadata columns)
    exclude_cols = [target_col, 'polymer_name', 'smiles', 'polymer_class']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if len(feature_cols) == 0:
        raise DataInsufficientError("No feature columns found in the dataset.")
    
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]
    
    if len(X) < 10:
        raise DataInsufficientError(
            f"Insufficient data for cross-validation. Found {len(X)} samples, "
            f"minimum 10 required."
        )
    
    return X, y


def load_model(path: Path):
    """
    Load the trained model from disk.
    
    Args:
        path: Path to the model pickle file.
        
    Returns:
        The loaded model object.
        
    Raises:
        DataInsufficientError: If the model file doesn't exist.
    """
    if not path.exists():
        raise DataInsufficientError(f"Model file not found at {path}")
    
    with open(path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Model loaded successfully from {path}")
    return model


def perform_stratified_cv(
    X: pd.DataFrame,
    y: pd.Series,
    model,
    n_folds: int = DEFAULT_N_FOLDS,
    random_state: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Perform stratified k-fold cross-validation.
    
    Stratification is based on discretized target values to ensure each fold
    has a representative distribution of performance values.
    
    Args:
        X: Feature matrix.
        y: Target variable.
        model: Trained model to evaluate.
        n_folds: Number of CV folds.
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing CV results.
    """
    logger.info(f"Starting stratified {n_folds}-fold cross-validation")
    
    # Discretize y for stratification
    # Use quantile-based binning to ensure balanced folds
    n_bins = min(n_folds, len(y.unique()))
    if n_bins < 2:
        logger.warning("Not enough unique target values for stratification. Using random split.")
        y_bins = pd.Series([0] * len(y))
    else:
        y_bins = pd.qcut(y, q=n_bins, labels=False, duplicates='drop')
        # Handle edge case where qcut might produce fewer bins than requested
        if len(y_bins.unique()) < 2:
            y_bins = pd.Series([0] * len(y))
    
    # Setup stratified k-fold
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=random_state)
    
    r2_scores = []
    mae_scores = []
    y_true_all = []
    y_pred_all = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y_bins)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Clone the model for this fold if it supports it, otherwise use the same one
        # For simplicity, we refit on each fold using the original model's parameters
        # Note: This assumes the model has a fit/predict interface
        try:
            # Deep copy the model to avoid state leakage between folds
            import copy
            fold_model = copy.deepcopy(model)
            fold_model.fit(X_train, y_train)
            
            y_pred = fold_model.predict(X_test)
            
            # Calculate metrics
            r2 = r2_score(y_test, y_pred)
            mae = mean_absolute_error(y_test, y_pred)
            
            r2_scores.append(r2)
            mae_scores.append(mae)
            y_true_all.extend(y_test.tolist())
            y_pred_all.extend(y_pred.tolist())
            
            logger.info(f"Fold {fold_idx + 1}/{n_folds}: R² = {r2:.4f}, MAE = {mae:.4f}")
            
        except Exception as e:
            logger.error(f"Error in fold {fold_idx + 1}: {str(e)}")
            raise
    
    # Calculate aggregate metrics
    results = {
        "n_folds": n_folds,
        "r2_scores": r2_scores,
        "r2_mean": float(np.mean(r2_scores)),
        "r2_std": float(np.std(r2_scores)),
        "mae_scores": mae_scores,
        "mae_mean": float(np.mean(mae_scores)),
        "mae_std": float(np.std(mae_scores)),
        "total_samples": len(y),
        "timestamp": datetime.now().isoformat(),
        "fold_details": [
            {
                "fold": i + 1,
                "r2": float(score),
                "mae": float(mae_scores[i])
            }
            for i, score in enumerate(r2_scores)
        ]
    }
    
    logger.info(f"Cross-validation complete. Mean R²: {results['r2_mean']:.4f} ± {results['r2_std']:.4f}")
    logger.info(f"Mean MAE: {results['mae_mean']:.4f} ± {results['mae_std']:.4f}")
    
    return results


def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save cross-validation results to a JSON file.
    
    Args:
        results: Dictionary of CV results.
        output_path: Path to save the results JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Cross-validation results saved to {output_path}")


def main() -> int:
    """
    Main entry point for cross-validation execution.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    setup_pipeline_logger()
    
    try:
        logger.info("Starting cross-validation pipeline")
        
        # Load data
        if not FEATURE_MATRIX_PATH.exists():
            logger.error(f"Feature matrix not found at {FEATURE_MATRIX_PATH}")
            logger.error("Please ensure T023 (feature matrix generation) has been completed first.")
            return 1
        
        X, y = load_feature_matrix(FEATURE_MATRIX_PATH)
        logger.info(f"Loaded {len(X)} samples for cross-validation")
        
        # Load model
        if not MODEL_PATH.exists():
            logger.error(f"Model not found at {MODEL_PATH}")
            logger.error("Please ensure T021 (model training) has been completed first.")
            return 1
        
        model = load_model(MODEL_PATH)
        
        # Perform cross-validation
        results = perform_stratified_cv(X, y, model)
        
        # Save results
        save_results(results, CROSS_VAL_RESULTS_PATH)
        
        # Print summary
        print("\n" + "="*50)
        print("CROSS-VALIDATION RESULTS")
        print("="*50)
        print(f"Total Samples: {results['total_samples']}")
        print(f"Folds: {results['n_folds']}")
        print(f"R² Score: {results['r2_mean']:.4f} ± {results['r2_std']:.4f}")
        print(f"MAE: {results['mae_mean']:.4f} ± {results['mae_std']:.4f}")
        print(f"Results saved to: {CROSS_VAL_RESULTS_PATH}")
        print("="*50 + "\n")
        
        return 0
        
    except DataInsufficientError as e:
        logger.error(f"Data insufficient error: {str(e)}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during cross-validation: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())