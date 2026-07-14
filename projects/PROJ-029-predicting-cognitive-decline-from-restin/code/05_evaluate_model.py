"""
Task T024: Evaluate the trained Random Forest model on nested CV folds.
Calculates ROC-AUC, accuracy, and F1-score per fold and mean.
Outputs: data/processed/performance_report.json
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
from sklearn.ensemble import RandomForestClassifier

# Import shared utilities from the project API surface
# Note: We import from utils.io for file handling consistency
# and utils.logger for logging if needed, though we keep this script self-contained for robustness.
try:
    from utils.io import load_json, save_json, ensure_dir
except ImportError:
    # Fallback if utils.io is not fully implemented yet, use standard paths
    from pathlib import Path
    import json
    
    def ensure_dir(p: Path) -> None:
        p.mkdir(parents=True, exist_ok=True)

    def load_json(p: Path) -> Any:
        with open(p, 'r') as f:
            return json.load(f)

    def save_json(p: Path, data: Any) -> None:
        ensure_dir(p.parent)
        with open(p, 'w') as f:
            json.dump(data, f, indent=2, default=str)

from utils.logger import get_logger, log_operation

# Constants
DATA_DIR = Path("data/processed")
MODEL_PATH = DATA_DIR / "model.pkl"
CV_RESULTS_PATH = DATA_DIR / "cv_results.json"
PERFORMANCE_REPORT_PATH = DATA_DIR / "performance_report.json"
ELIGIBLE_SUBJECTS_PATH = DATA_DIR / "eligible_subjects.csv"
GRAPH_METRICS_PATH = DATA_DIR / "graph_metrics.csv"

logger = get_logger("evaluate_model")

def ensure_file(path: Path) -> None:
    """Ensure a file exists, raising a clear error if not."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")

def isnan(val: Any) -> bool:
    """Check for NaN values safely."""
    if isinstance(val, float):
        return np.isnan(val)
    if isinstance(val, (list, np.ndarray)):
        return any(np.isnan(v) if isinstance(v, float) else False for v in val)
    return False

def load_eligible_subjects() -> List[str]:
    """Load the list of eligible subject IDs."""
    ensure_file(ELIGIBLE_SUBJECTS_PATH)
    df = pd.read_csv(ELIGIBLE_SUBJECTS_PATH)
    # Assume column 'subject_id' or similar; check common names
    if 'subject_id' in df.columns:
        return df['subject_id'].astype(str).tolist()
    elif 'participant_id' in df.columns:
        return df['participant_id'].astype(str).tolist()
    else:
        # Fallback: assume first column is ID
        return df.iloc[:, 0].astype(str).tolist()

def load_features() -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load features and labels.
    This assumes code/04_train_model.py has already processed the data and saved
    the necessary artifacts or that we can reconstruct them from graph_metrics.csv.
    For T024, we assume the model was trained on features derived from graph_metrics.csv
    and labels from the decline definition.
    
    Since T023 (train_model) is the producer of model.pkl and cv_results.json,
    we assume the model object contains the necessary preprocessing or we load
    the raw features from graph_metrics.csv and re-apply the logic if needed.
    
    However, the standard pattern for T024 is to load the *results* of the CV
    from cv_results.json if available, or re-evaluate the saved model if the
    split data is available.
    
    Given the constraints and the "atomize" history of T023, we will implement
    a robust evaluation that:
    1. Loads the trained model from model.pkl.
    2. Loads the graph_metrics.csv.
    3. Reconstructs the X, y if labels are present in the metrics file or if
       we can infer them from the eligible subjects list and the original data.
    
    CRITICAL: The task description says "Calculate ROC-AUC... per fold".
    This implies we need the fold-specific predictions.
    If T023 wrote cv_results.json with fold-level predictions, we load that.
    If not, we must re-run the inference on the held-out data if available.
    
    Strategy:
    - Try to load cv_results.json which should contain fold metrics.
    - If that fails (T023 incomplete), we load model.pkl and graph_metrics.csv,
      and if the decline label is in graph_metrics.csv (or we can compute it),
      we perform a single evaluation or a simple CV if the split indices are known.
    
    To satisfy the "per fold" requirement without re-implementing the whole CV loop:
    We assume T023 wrote cv_results.json with keys like 'fold_0', 'fold_1', etc.,
    containing 'roc_auc', 'accuracy', 'f1'.
    If cv_results.json is missing, we attempt to generate a minimal report based
    on the available model and data, noting the limitation.
    """
    
    # Attempt to load pre-computed CV results from T023
    if CV_RESULTS_PATH.exists():
        results = load_json(CV_RESULTS_PATH)
        # Return the results object directly if it contains the metrics
        return results, None 
    
    # Fallback: Load model and raw data to compute metrics if CV results missing
    # This path assumes we can compute the decline label from the raw data
    ensure_file(MODEL_PATH)
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    
    ensure_file(GRAPH_METRICS_PATH)
    df_metrics = pd.read_csv(GRAPH_METRICS_PATH)
    
    # We need to identify the target column.
    # Based on T023 description: "Define decline label (drop >= 3 points)".
    # We assume the graph_metrics.csv or a related file has the labels.
    # If not, we cannot compute metrics. We will raise an error if no label column found.
    possible_label_cols = ['decline_label', 'is_declined', 'target', 'label']
    label_col = None
    for col in possible_label_cols:
        if col in df_metrics.columns:
            label_col = col
            break
    
    if label_col is None:
        # Try to infer from column names containing 'label' or 'score'
        for col in df_metrics.columns:
            if 'label' in col.lower() or 'target' in col.lower():
                label_col = col
                break
    
    if label_col is None:
        logger.log("error", message="No target label column found in graph_metrics.csv")
        raise ValueError("Cannot evaluate model: No target label found in data.")
    
    X = df_metrics.drop(columns=[label_col, 'subject_id', 'participant_id', 'id'], errors='ignore')
    y = df_metrics[label_col]
    
    # If we have the model, we can compute metrics on the whole set (not per fold)
    # But the task asks for per-fold. Without fold indices, we can only do a global eval.
    # We will compute global metrics and note the lack of per-fold data.
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None
    
    return {
        "X": X,
        "y": y,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "model": model
    }, None

def split_features_labels(data: Any) -> Tuple[pd.DataFrame, pd.Series]:
    """Helper to extract X and y if data is a dict."""
    if isinstance(data, dict) and 'X' in data and 'y' in data:
        return data['X'], data['y']
    return None, None

def calculate_metrics(y_true: pd.Series, y_pred: np.ndarray, y_prob: np.ndarray = None) -> Dict[str, float]:
    """Calculate ROC-AUC, accuracy, and F1-score."""
    metrics = {}
    
    # Accuracy
    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    
    # F1-score
    metrics['f1_score'] = float(f1_score(y_true, y_pred, zero_division=0))
    
    # ROC-AUC
    if y_prob is not None:
        # Ensure binary classification for ROC-AUC
        if len(np.unique(y_true)) > 1:
            try:
                metrics['roc_auc'] = float(roc_auc_score(y_true, y_prob))
            except ValueError:
                metrics['roc_auc'] = float('nan')
        else:
            metrics['roc_auc'] = float('nan')
    else:
        metrics['roc_auc'] = float('nan')
    
    return metrics

def evaluate_model(cv_results: Any, data_payload: Any = None) -> Dict[str, Any]:
    """
    Evaluate the model and aggregate metrics.
    If cv_results contains fold-level data, use that.
    Otherwise, compute from data_payload.
    """
    report = {
        "folds": [],
        "mean_metrics": {},
        "status": "completed",
        "notes": []
    }

    # Case 1: We have pre-computed CV results from T023
    if isinstance(cv_results, dict) and 'folds' in cv_results:
        folds_data = cv_results['folds']
        for fold_idx, fold_data in enumerate(folds_data):
            fold_metrics = {
                "fold": fold_idx,
                "roc_auc": fold_data.get('roc_auc', float('nan')),
                "accuracy": fold_data.get('accuracy', float('nan')),
                "f1_score": fold_data.get('f1_score', float('nan'))
            }
            report["folds"].append(fold_metrics)
        
        # Calculate means
        roc_aucs = [f['roc_auc'] for f in report["folds"] if not isnan(f['roc_auc'])]
        accuracies = [f['accuracy'] for f in report["folds"] if not isnan(f['accuracy'])]
        f1_scores = [f['f1_score'] for f in report["folds"] if not isnan(f['f1_score'])]
        
        report["mean_metrics"] = {
            "roc_auc": np.mean(roc_aucs) if roc_aucs else float('nan'),
            "accuracy": np.mean(accuracies) if accuracies else float('nan'),
            "f1_score": np.mean(f1_scores) if f1_scores else float('nan')
        }
        
    # Case 2: We have raw data and model (fallback if T023 didn't write fold details)
    elif data_payload is not None:
        X, y = split_features_labels(data_payload)
        if X is None or y is None:
            raise ValueError("Could not extract features and labels from data payload.")
        
        y_pred = data_payload.get('y_pred')
        y_prob = data_payload.get('y_prob')
        
        if y_pred is None:
            raise ValueError("Predictions not found in data payload.")
        
        # Compute single set of metrics (simulating a single fold or global)
        # Since we don't have fold indices, we report this as a global evaluation
        # and note it in the report.
        metrics = calculate_metrics(y, y_pred, y_prob)
        
        report["folds"].append({
            "fold": 0,
            "roc_auc": metrics['roc_auc'],
            "accuracy": metrics['accuracy'],
            "f1_score": metrics['f1_score']
        })
        
        report["mean_metrics"] = metrics
        report["notes"].append("Metrics computed on full dataset (no fold split available in input).")
        
    else:
        report["status"] = "failed"
        report["notes"].append("No valid evaluation data found.")
    
    return report

def write_performance_report(report: Dict[str, Any]) -> None:
    """Write the performance report to JSON."""
    ensure_dir(PERFORMANCE_REPORT_PATH)
    save_json(PERFORMANCE_REPORT_PATH, report)
    logger.log("info", message=f"Performance report written to {PERFORMANCE_REPORT_PATH}")

def main() -> int:
    """Main entry point for T024."""
    logger.log("start", operation="evaluate_model_main")
    
    try:
        # 1. Load data and model
        # We try to load cv_results.json first (produced by T023)
        cv_results = None
        if CV_RESULTS_PATH.exists():
            try:
                cv_results = load_json(CV_RESULTS_PATH)
                logger.log("info", message="Loaded CV results from T023")
            except Exception as e:
                logger.log("warning", message=f"Failed to load CV results: {e}")
                cv_results = None
        
        data_payload = None
        if cv_results is None:
            # Fallback: Load model and data to compute metrics
            logger.log("info", message="CV results not found, attempting fallback evaluation")
            try:
                # We need to load the model and data to compute metrics manually
                # This requires the model to be pickled and the data to be available
                ensure_file(MODEL_PATH)
                with open(MODEL_PATH, 'rb') as f:
                    model = pickle.load(f)
                
                ensure_file(GRAPH_METRICS_PATH)
                df_metrics = pd.read_csv(GRAPH_METRICS_PATH)
                
                # Identify label column
                label_col = None
                possible_cols = ['decline_label', 'is_declined', 'target', 'label']
                for col in possible_cols:
                    if col in df_metrics.columns:
                        label_col = col
                        break
                
                if label_col is None:
                    logger.log("error", message="Target label column not found in graph_metrics.csv")
                    # Create a minimal report indicating failure
                    report = {
                        "folds": [],
                        "mean_metrics": {"roc_auc": float('nan'), "accuracy": float('nan'), "f1_score": float('nan')},
                        "status": "failed",
                        "notes": ["Target label column not found"]
                    }
                    write_performance_report(report)
                    return 1
                
                X = df_metrics.drop(columns=[label_col, 'subject_id', 'participant_id', 'id'], errors='ignore')
                y = df_metrics[label_col]
                
                y_pred = model.predict(X)
                y_prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None
                
                data_payload = {
                    "X": X,
                    "y": y,
                    "y_pred": y_pred,
                    "y_prob": y_prob
                }
            except Exception as e:
                logger.log("error", message=f"Fallback evaluation failed: {e}")
                report = {
                    "folds": [],
                    "mean_metrics": {"roc_auc": float('nan'), "accuracy": float('nan'), "f1_score": float('nan')},
                    "status": "failed",
                    "notes": [f"Evaluation failed: {str(e)}"]
                }
                write_performance_report(report)
                return 1
        
        # 2. Evaluate
        report = evaluate_model(cv_results, data_payload)
        
        # 3. Write report
        write_performance_report(report)
        
        logger.log("finish", operation="evaluate_model_main", status="success")
        return 0
        
    except Exception as e:
        logger.log("error", message=f"Evaluation failed: {str(e)}")
        # Write a failure report
        report = {
            "folds": [],
            "mean_metrics": {"roc_auc": float('nan'), "accuracy": float('nan'), "f1_score": float('nan')},
            "status": "failed",
            "notes": [str(e)]
        }
        write_performance_report(report)
        return 1

if __name__ == "__main__":
    sys.exit(main())