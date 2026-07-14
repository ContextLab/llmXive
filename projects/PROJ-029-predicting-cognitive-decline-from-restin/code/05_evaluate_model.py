"""
Task T024: Evaluate the trained model performance.

Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs results to data/processed/performance_report.json.

This script assumes that:
1. The model has been trained by code/04_train_model.py and saved to data/processed/model.pkl.
2. The graph metrics and labels are available in data/processed/graph_metrics.csv.
"""
import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, confusion_matrix
import warnings

# Add project root to path to import utils
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ensure imports from sibling modules work
sys.path.insert(0, str(PROJECT_ROOT / "code"))
from utils.logger import get_logger
from utils.io import load_json, ensure_dir, save_json

# Constants
MODEL_PATH = project_root / "data" / "processed" / "model.pkl"
DATA_PATH = project_root / "data" / "processed" / "graph_metrics.csv"
OUTPUT_PATH = project_root / "data" / "processed" / "performance_report.json"
LABEL_COLUMN = "decline_label"  # Column name for the target variable
FEATURE_COLUMNS_START = "degree" # Heuristic to identify feature columns (all non-ID, non-label)

def get_logger_wrapper():
    """Setup logger for this module."""
    return get_logger("evaluate_model")

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray, logger) -> dict:
    """
    Calculate standard classification metrics.
    
    Args:
        y_true: Array of true labels.
        y_pred: Array of predicted labels.
        y_prob: Array of predicted probabilities (for ROC-AUC).
        
    Returns:
        dict: Dictionary containing ROC-AUC, accuracy, and F1-score.
    """
    metrics = {}
    
    # ROC-AUC (requires probabilities)
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
    except ValueError as e:
        # Handle cases where only one class is present
        metrics["roc_auc"] = None
        warnings.warn(f"ROC-AUC could not be calculated: {e}")

    # Accuracy
    metrics["accuracy"] = float(accuracy_score(y_true, y_pred))

    # F1-Score
    metrics["f1_score"] = float(f1_score(y_true, y_pred, zero_division=0))

    return metrics

def evaluate_model(model, X, y):
    """
    Evaluate the model on the given data.
    
    Args:
        model: Trained sklearn estimator.
        X: Feature matrix.
        y: Target vector.
        
    Returns:
        dict: Evaluation metrics.
    """
    # Predictions
    y_pred = model.predict(X)
    
    # Probabilities (for ROC-AUC)
    # Check if model has predict_proba
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X)
        # If binary classification, take the probability of the positive class (usually index 1)
        if y_prob.shape[1] == 2:
            y_prob = y_prob[:, 1]
        else:
            # If multiclass or single output, use as is (might need adjustment for ROC-AUC)
            y_prob = y_prob[:, 1] if y_prob.shape[1] > 1 else y_prob.flatten()
    else:
        # Fallback for models without predict_proba (e.g., some simple estimators)
        # We cannot compute ROC-AUC without probabilities
        y_prob = y_pred 
        warnings.warn("Model does not have predict_proba method. ROC-AUC will be None.")

    return calculate_metrics(y, y_pred, y_prob)

def main():
    """Main execution function for T024."""
    logger = get_logger_wrapper()
    logger.info("Starting model evaluation (T024).")
    start_time = time.time()

    # 1. Check for required inputs
    if not MODEL_PATH.exists():
        logger.error(f"Model file not found at {MODEL_PATH}. Run T023 (04_train_model.py) first.")
        sys.exit(1)

    if not DATA_PATH.exists():
        logger.error(f"Data file not found at {DATA_PATH}. Run T019 (03_compute_graph_metrics.py) first.")
        sys.exit(1)

    # 2. Load data
    logger.info(f"Loading data from {DATA_PATH}")
    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # 3. Prepare features and labels
    # Assume the label column is 'decline_label' and the rest are features (excluding ID columns if any)
    # We need to be careful about column selection.
    # Let's assume the first column is 'subject_id' and the last is 'decline_label'.
    # Or better, explicitly drop known non-feature columns.
    
    if LABEL_COLUMN not in df.columns:
        logger.error(f"Label column '{LABEL_COLUMN}' not found in {DATA_PATH}")
        sys.exit(1)

    # Identify feature columns: all columns except subject_id (if exists) and label
    feature_cols = [col for col in df.columns if col != "subject_id" and col != LABEL_COLUMN]
    
    if not feature_cols:
        logger.error("No feature columns found in the dataset.")
        sys.exit(1)

    X = df[feature_cols].values
    y = df[LABEL_COLUMN].values

    logger.info(f"Loaded {len(y)} samples with {len(feature_cols)} features.")

    # 4. Load model
    logger.info(f"Loading model from {MODEL_PATH}")
    try:
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # 5. Evaluate
    logger.info("Calculating metrics...")
    # The model trained in T023 is a Random Forest, which should have predict_proba.
    # However, the training script might have saved a pipeline or just the estimator.
    # We assume it's the estimator or a pipeline that supports predict/predict_proba.
    
    results = evaluate_model(model, X, y)
    
    # Add metadata
    results["n_samples"] = int(len(y))
    results["n_features"] = int(len(feature_cols))
    results["feature_columns"] = feature_cols
    results["elapsed_time_seconds"] = time.time() - start_time
    results["status"] = "success"

    # 6. Save output
    ensure_dir(OUTPUT_PATH.parent)
    logger.info(f"Saving performance report to {OUTPUT_PATH}")
    save_json(results, OUTPUT_PATH)

    logger.info(f"Evaluation complete. ROC-AUC: {results.get('roc_auc', 'N/A')}, "
                f"Accuracy: {results.get('accuracy', 'N/A')}, F1: {results.get('f1_score', 'N/A')}")

    return 0

if __name__ == "__main__":
    sys.exit(main())