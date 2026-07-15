"""
code/05_evaluate_model.py
Task T024: Evaluate the trained model.

Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs results to data/processed/performance_report.json.

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
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, classification_report

# Import shared utilities from project structure
# Note: We import from the utils package as defined in the API surface
from utils.io import load_json, save_json, load_csv
from utils.logger import get_logger, log_operation

# Configuration
MODEL_PATH = Path("data/processed/model.pkl")
GRAPH_METRICS_PATH = Path("data/processed/graph_metrics.csv")
ELIGIBLE_SUBJECTS_PATH = Path("data/processed/eligible_subjects.csv")
OUTPUT_PATH = Path("data/processed/performance_report.json")

# Ensure output directory exists
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = get_logger("evaluate_model")

def ensure_file(path: Path) -> None:
    """Check if a required file exists."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

def isnan(value: Any) -> bool:
    """Check if a value is NaN."""
    if isinstance(value, float):
        return np.isnan(value)
    if isinstance(value, (list, np.ndarray)):
        return any(np.isnan(v) for v in value if isinstance(v, float))
    return False

@log_operation("load_eligible_subjects")
def load_eligible_subjects(path: Path) -> List[str]:
    """
    Load subject IDs from the eligible subjects CSV.
    Returns a list of subject IDs.
    """
    ensure_file(path)
    try:
        df = pd.read_csv(path)
        # Handle potential schema variations
        if "subject_id" in df.columns:
            subjects = df["subject_id"].astype(str).tolist()
        elif "participant_id" in df.columns:
            subjects = df["participant_id"].astype(str).tolist()
        elif "sub" in df.columns:
            subjects = df["sub"].astype(str).tolist()
        else:
            # Fallback: use first column if only one exists
            if len(df.columns) > 0:
                subjects = df.iloc[:, 0].astype(str).tolist()
            else:
                raise ValueError(f"CSV {path} has no data columns.")
        
        if not subjects:
            logger.log("warning", message="No subjects found in eligible list.")
            return []
        
        return subjects
    except Exception as e:
        logger.log("error", message=f"Failed to load eligible subjects: {str(e)}")
        raise

@log_operation("load_features")
def load_features(metrics_path: Path, subjects: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load graph metrics and labels for the specified subjects.
    Returns (X, y) where X is features and y is the decline label.
    """
    ensure_file(metrics_path)
    df = pd.read_csv(metrics_path)
    
    # Identify the label column. 
    # Based on T023, the label is likely 'decline_label' or derived from MMSE/MOCA change.
    # We assume the CSV contains a 'decline_label' column or we calculate it.
    label_col = None
    for candidate in ["decline_label", "label", "y", "outcome"]:
        if candidate in df.columns:
            label_col = candidate
            break
    
    if label_col is None:
        # If no explicit label column, we might need to calculate it from MMSE/MOCA
        # However, for T024, we assume T023 has already prepared the data with a label.
        # If the file is empty or missing the label, we fail loudly.
        raise ValueError(
            f"Label column not found in {metrics_path}. "
            f"Available columns: {list(df.columns)}. "
            f"Ensure T023 (train_model.py) has written the label column."
        )
    
    # Filter for subjects in the eligible list
    # Assume subject ID column is 'subject_id' or similar
    subject_col = None
    for candidate in ["subject_id", "participant_id", "sub", "id"]:
        if candidate in df.columns:
            subject_col = candidate
            break
    
    if subject_col is None:
        raise ValueError(f"Subject ID column not found in {metrics_path}.")
    
    # Filter dataframe
    mask = df[subject_col].isin(subjects)
    df_filtered = df[mask].sort_values(by=subject_col)
    
    if len(df_filtered) == 0:
        raise ValueError(f"No matching subjects found in {metrics_path} for the eligible list.")
    
    # Separate features and label
    # Features are all columns except the subject ID and the label
    feature_cols = [c for c in df_filtered.columns if c not in [subject_col, label_col]]
    
    if not feature_cols:
        raise ValueError(f"No feature columns found in {metrics_path}.")
    
    X = df_filtered[feature_cols].values
    y = df_filtered[label_col].values
    
    # Handle any NaNs in features
    if np.any(np.isnan(X)):
        logger.log("warning", message="NaN values detected in features. Replacing with 0.")
        X = np.nan_to_num(X, nan=0.0)
    
    return X, y

@log_operation("split_features_labels")
def split_features_labels(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Ensure X and y are properly shaped.
    """
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    return X, y

@log_operation("calculate_metrics")
def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, float]:
    """
    Calculate ROC-AUC, accuracy, and F1-score.
    """
    metrics = {}
    
    # ROC-AUC
    try:
        # Ensure we have probabilities for ROC-AUC
        if y_prob is not None and len(np.unique(y_true)) > 1:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        else:
            metrics["roc_auc"] = float("nan")
    except Exception as e:
        logger.log("error", message=f"Failed to calculate ROC-AUC: {str(e)}")
        metrics["roc_auc"] = float("nan")
    
    # Accuracy
    try:
        metrics["accuracy"] = float(accuracy_score(y_true, y_pred))
    except Exception as e:
        logger.log("error", message=f"Failed to calculate accuracy: {str(e)}")
        metrics["accuracy"] = float("nan")
    
    # F1-score
    try:
        # Handle binary classification
        metrics["f1"] = float(f1_score(y_true, y_pred, zero_division=0))
    except Exception as e:
        logger.log("error", message=f"Failed to calculate F1-score: {str(e)}")
        metrics["f1"] = float("nan")
    
    return metrics

@log_operation("evaluate_model")
def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Evaluate the model on the given data.
    Returns a dictionary with metrics and predictions.
    """
    # Get predictions
    y_pred = model.predict(X)
    
    # Get probabilities (if available)
    y_prob = None
    if hasattr(model, "predict_proba"):
        try:
            y_prob = model.predict_proba(X)[:, 1]
        except Exception as e:
            logger.log("warning", message=f"Could not get probabilities: {str(e)}")
    
    # Calculate metrics
    metrics = calculate_metrics(y, y_pred, y_prob)
    
    return {
        "metrics": metrics,
        "y_true": y.tolist(),
        "y_pred": y_pred.tolist(),
        "y_prob": y_prob.tolist() if y_prob is not None else None
    }

@log_operation("write_performance_report")
def write_performance_report(results: Dict[str, Any], path: Path) -> None:
    """
    Write the performance report to a JSON file.
    """
    # Ensure the directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format the report
    report = {
        "status": "success",
        "output_file": str(path),
        "results": results
    }
    
    try:
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.log("info", message=f"Performance report written to {path}")
    except Exception as e:
        logger.log("error", message=f"Failed to write performance report: {str(e)}")
        raise

@log_operation("evaluate_model_main")
def main() -> int:
    """
    Main entry point for the evaluation script.
    """
    logger.log("start", operation="evaluate_model_main", message="Starting model evaluation")
    
    try:
        # 1. Load the trained model
        logger.log("info", message="Loading model from disk")
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}. "
                                  "Please ensure T023 (train_model.py) has run successfully.")
        
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        
        # 2. Load eligible subjects
        logger.log("info", message="Loading eligible subjects")
        if not ELIGIBLE_SUBJECTS_PATH.exists():
            # If eligible subjects file doesn't exist, try to load from graph metrics directly
            # This handles the case where T017 failed to produce the file but T019/T023 did
            subjects = None
        else:
            subjects = load_eligible_subjects(ELIGIBLE_SUBJECTS_PATH)
        
        # 3. Load features and labels
        logger.log("info", message="Loading features and labels")
        X, y = load_features(GRAPH_METRICS_PATH, subjects)
        
        # 4. Evaluate the model
        logger.log("info", message="Evaluating model")
        results = evaluate_model(model, X, y)
        
        # 5. Write the performance report
        logger.log("info", message="Writing performance report")
        write_performance_report(results, OUTPUT_PATH)
        
        # 6. Print summary
        print(f"Evaluation complete. Results saved to {OUTPUT_PATH}")
        print(f"ROC-AUC: {results['metrics']['roc_auc']:.4f}")
        print(f"Accuracy: {results['metrics']['accuracy']:.4f}")
        print(f"F1-score: {results['metrics']['f1']:.4f}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.log("error", message=str(e))
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.log("error", message=f"Unexpected error: {str(e)}")
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())