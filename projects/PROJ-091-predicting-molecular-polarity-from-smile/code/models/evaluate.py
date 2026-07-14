"""
Model Evaluation Module for Molecular Polarity Prediction.

This module computes R², RMSE, and compares the model performance against a null model (R²=0).
It loads data from the split files and the trained model to perform these evaluations.
"""

import os
import sys
import logging
import pickle
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import r2_score, mean_squared_error

# Project imports
from utils.logging_config import get_logger, set_log_level
from data.split_data import load_splits

logger = get_logger(__name__)


def compute_null_model_r2(y_true: np.ndarray) -> float:
    """
    Computes the R² score of a null model (predicting the mean of y_true).
    By definition, the R² of a null model (mean predictor) is 0.0.
    
    Args:
        y_true: Array of true target values.
    
    Returns:
        float: The R² score of the null model (always 0.0).
    """
    # The null model predicts the mean of y for all instances.
    # R² = 1 - (SS_res / SS_tot)
    # SS_res = sum((y_true - mean(y))**2)
    # SS_tot = sum((y_true - mean(y))**2)
    # Therefore, R² = 0.
    return 0.0


def evaluate_model(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str = "LightGBM"
) -> Dict[str, float]:
    """
    Evaluates the model performance using R² and RMSE, and compares against a null model.
    
    Args:
        y_true: Array of true target values (dipole moments).
        y_pred: Array of predicted target values.
        model_name: Name of the model being evaluated (for logging).
    
    Returns:
        dict: A dictionary containing 'r2', 'rmse', 'null_model_r2', and 'outperforms_null'.
    """
    if len(y_true) == 0:
        raise ValueError("y_true is empty. Cannot evaluate model.")
    
    # Calculate metrics
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    null_r2 = compute_null_model_r2(y_true)
    
    # Compare against null model
    # A model outperforms the null model if R² > 0
    outperforms_null = r2 > null_r2
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse),
        "null_model_r2": float(null_r2),
        "outperforms_null": outperforms_null,
        "model_name": model_name,
        "n_samples": int(len(y_true))
    }
    
    logger.info(f"Evaluation Results for {model_name}:")
    logger.info(f"  R² Score: {r2:.4f}")
    logger.info(f"  RMSE: {rmse:.4f}")
    logger.info(f"  Null Model R²: {null_r2:.4f}")
    logger.info(f"  Outperforms Null Model: {outperforms_null}")
    
    return metrics


def load_evaluation_data(
    splits_path: Path,
    features_path: Optional[Path] = None,
    target_col: str = "dipole_moment"
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Loads the test set data (features and targets) from the split files.
    
    Args:
        splits_path: Path to the directory containing split indices (e.g., test_indices.npy).
        features_path: Path to the processed descriptors parquet file. If None, it assumes
                       the default path relative to the project root.
        target_col: Name of the target column in the dataset.
    
    Returns:
        Tuple[np.ndarray, np.ndarray]: (y_true, y_pred_placeholder) - actually just y_true here,
                                       but the function signature prepares for future prediction loading
                                       or direct model inference.
    """
    # Default path if not provided
    if features_path is None:
        features_path = Path("data/processed/descriptors.parquet")
    
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found at {features_path}")
    
    # Load full dataset
    df = pd.read_parquet(features_path)
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in {features_path}")
    
    # Load test indices
    test_indices_path = splits_path / "test_indices.npy"
    if not test_indices_path.exists():
        raise FileNotFoundError(f"Test indices not found at {test_indices_path}")
    
    test_indices = np.load(test_indices_path)
    
    # Filter dataframe for test set
    test_df = df.iloc[test_indices]
    
    y_true = test_df[target_col].values
    
    logger.info(f"Loaded {len(y_true)} test samples from {features_path}")
    
    return y_true, test_df


def run_evaluation(
    model_path: Path,
    splits_dir: Path,
    features_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Orchestrates the full evaluation process: loads model, loads test data, predicts,
    computes metrics, and saves results.
    
    Args:
        model_path: Path to the pickled model file.
        splits_dir: Directory containing split indices (train_indices.npy, test_indices.npy).
        features_path: Path to the processed descriptors parquet file.
        output_path: Path to save the evaluation results JSON. Defaults to data/processed/evaluation_results.json.
    
    Returns:
        dict: The evaluation metrics dictionary.
    """
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")
    
    # Load model
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    # Load test data
    y_true, test_features_df = load_evaluation_data(
        splits_dir, features_path=features_path
    )
    
    # Predict
    logger.info("Generating predictions on test set...")
    y_pred = model.predict(test_features_df)
    
    # Evaluate
    metrics = evaluate_model(y_true, y_pred)
    
    # Save results
    if output_path is None:
        output_path = Path("data/processed/evaluation_results.json")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")
    
    return metrics


def main():
    """
    Entry point for the evaluation script.
    """
    # Setup logging
    set_log_level(logging.INFO)
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parents[2]
    model_path = project_root / "data/processed/model.pkl"
    splits_dir = project_root / "data/processed"
    features_path = project_root / "data/processed/descriptors.parquet"
    output_path = project_root / "data/processed/evaluation_results.json"
    
    try:
        metrics = run_evaluation(model_path, splits_dir, features_path, output_path)
        
        # Exit with error code if model does not outperform null model
        if not metrics["outperforms_null"]:
            logger.error("Model failed to outperform the null model (R² <= 0).")
            sys.exit(1)
        
        logger.info("Evaluation completed successfully.")
        sys.exit(0)
        
    except Exception as e:
        logger.exception(f"Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()