"""
T024: Evaluate the trained model and generate performance report.

Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs to data/processed/performance_report.json.

Prerequisites:
    - data/processed/model.pkl (from T023)
    - data/processed/graph_metrics.csv (from T019)
    - data/processed/eligible_subjects.csv (from T017)
"""
from __future__ import annotations

import json
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score
from sklearn.model_selection import cross_val_predict
from sklearn.base import clone

# Import from project utils
from utils.logger import get_logger, log_operation
from utils.io import load_json, ensure_dir

# Constants
MODEL_PATH = Path("data/processed/model.pkl")
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
PERFORMANCE_REPORT_PATH = Path("data/processed/performance_report.json")
RANDOM_SEED = 42

logger = get_logger("evaluate_model")


def ensure_file(path: Path) -> None:
    """Ensure the parent directory of a path exists."""
    ensure_dir(str(path))


def isnan(value: Any) -> bool:
    """Check if a value is NaN safely."""
    try:
        return np.isnan(value)
    except (TypeError, ValueError):
        return False


def load_eligible_subjects() -> List[str]:
    """Load the list of eligible subject IDs."""
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
    
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    # Assume the column is 'subject_id' based on T017 output
    if 'subject_id' in df.columns:
        return df['subject_id'].astype(str).tolist()
    elif 'participant_id' in df.columns:
        return df['participant_id'].astype(str).tolist()
    else:
        # Fallback: assume first column is ID
        return df.iloc[:, 0].astype(str).tolist()


def load_features() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load graph metrics and labels.
    
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Labels (decline: 1, no decline: 0)
        feature_names: List of feature column names
    """
    if not GRAPH_METRICS_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
    
    df = pd.read_csv(GRAPH_METRICS_PATH)
    
    # Identify label column
    label_col = None
    for col in ['decline_label', 'label', 'y', 'cognitive_decline']:
        if col in df.columns:
            label_col = col
            break
    
    if label_col is None:
        # Try to find a column that looks like a binary label
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].nunique() == 2:
                label_col = col
                break
    
    if label_col is None:
        raise ValueError("Could not find a binary label column in graph metrics.")
    
    # Separate features and labels
    feature_cols = [c for c in df.columns if c != label_col]
    # Ensure we only use numeric features
    numeric_feature_cols = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    
    X = df[numeric_feature_cols].values
    y = df[label_col].values
    
    return X, y, numeric_feature_cols


def split_features_labels(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Simple wrapper to ensure types are correct."""
    return np.array(X), np.array(y)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """
    Calculate ROC-AUC, accuracy, and F1-score.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels (0 or 1)
        y_prob: Predicted probabilities for class 1
    
    Returns:
        Dictionary of metric names to values
    """
    metrics = {}
    
    # ROC-AUC
    try:
        metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
    except ValueError:
        # If only one class is present, AUC is undefined
        metrics['roc_auc'] = float('nan')
    
    # Accuracy
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    
    # F1-score
    metrics['f1_score'] = float(f1_score(y_true, y_pred, zero_division=0))
    
    return metrics


def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Evaluate model using cross-validation predictions.
    
    This function performs a 5-fold cross-validation to generate predictions
    for each sample, then calculates metrics on the out-of-fold predictions.
    
    Args:
        model: Trained sklearn model
        X: Feature matrix
        y: Labels
    
    Returns:
        Dictionary containing per-fold metrics and aggregate metrics
    """
    from sklearn.model_selection import StratifiedKFold
    
    n_splits = 5
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_SEED)
    
    all_y_true = []
    all_y_pred = []
    all_y_prob = []
    
    fold_metrics = []
    
    # Ensure we have both classes for stratification
    if len(np.unique(y)) < 2:
        logger.log("evaluate_model_skipped", reason="Only one class present in labels")
        return {
            "status": "skipped",
            "reason": "Only one class present in labels",
            "metrics": {}
        }
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Clone the model to avoid modifying the original
        fold_model = clone(model)
        fold_model.fit(X_train, y_train)
        
        # Predictions
        y_pred_fold = fold_model.predict(X_test)
        y_prob_fold = fold_model.predict_proba(X_test)[:, 1]
        
        # Calculate fold metrics
        fold_metrics.append(calculate_metrics(y_test, y_pred_fold, y_prob_fold))
        
        all_y_true.extend(y_test)
        all_y_pred.extend(y_pred_fold)
        all_y_prob.extend(y_prob_fold)
    
    # Aggregate metrics
    all_y_true = np.array(all_y_true)
    all_y_pred = np.array(all_y_pred)
    all_y_prob = np.array(all_y_prob)
    
    aggregate_metrics = calculate_metrics(all_y_true, all_y_pred, all_y_prob)
    
    return {
        "status": "success",
        "n_samples": len(all_y_true),
        "n_splits": n_splits,
        "fold_metrics": fold_metrics,
        "aggregate_metrics": aggregate_metrics
    }


def write_performance_report(results: Dict[str, Any], path: Path) -> None:
    """Write performance report to JSON file."""
    ensure_file(path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    logger.log("write_performance_report", path=str(path), status="success")


@log_operation("evaluate_model_main")
def main() -> int:
    """Main entry point for evaluation."""
    logger.log("start", message="Starting model evaluation")
    
    # Check prerequisites
    if not MODEL_PATH.exists():
        logger.log("error", message=f"Model file not found: {MODEL_PATH}")
        print(f"Error: Required model file not found: {MODEL_PATH}")
        return 1
    
    if not GRAPH_METRICS_PATH.exists():
        logger.log("error", message=f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
        print(f"Error: Required graph metrics file not found: {GRAPH_METRICS_PATH}")
        return 1
    
    if not ELIGIBLE_SUBJECTS_PATH.exists():
        logger.log("error", message=f"Eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        print(f"Error: Required eligible subjects file not found: {ELIGIBLE_SUBJECTS_PATH}")
        return 1
    
    try:
        # Load data
        logger.log("load_data", message="Loading features and labels")
        X, y, feature_names = load_features()
        logger.log("data_loaded", n_samples=len(X), n_features=len(feature_names))
        
        # Load model
        logger.log("load_model", path=str(MODEL_PATH))
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        
        # Evaluate
        logger.log("evaluate", message="Running cross-validation evaluation")
        results = evaluate_model(model, X, y)
        
        # Write report
        write_performance_report(results, PERFORMANCE_REPORT_PATH)
        
        logger.log("finish", message="Evaluation complete", output=str(PERFORMANCE_REPORT_PATH))
        print(f"Performance report written to: {PERFORMANCE_REPORT_PATH}")
        
        # Print summary
        if results.get("status") == "success":
            agg = results.get("aggregate_metrics", {})
            print(f"\nAggregate Metrics:")
            print(f"  ROC-AUC: {agg.get('roc_auc', 'N/A'):.4f}")
            print(f"  Accuracy: {agg.get('accuracy', 'N/A'):.4f}")
            print(f"  F1-Score: {agg.get('f1_score', 'N/A'):.4f}")
        
        return 0
        
    except Exception as e:
        logger.log("error", message=str(e), exc_info=True)
        print(f"Error during evaluation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())