"""
code/05_evaluate_model.py

Evaluate the trained Random Forest model using nested cross-validation results.
Calculates ROC-AUC, accuracy, and F1-score per fold and their means.
Outputs results to data/processed/performance_report.json.

Dependencies:
  - data/processed/model.pkl (produced by code/04_train_model.py)
  - data/processed/graph_metrics.csv (produced by code/03_compute_graph_metrics.py)
  - data/processed/eligible_subjects.csv (produced by code/01_download_and_filter.py)
  - data/processed/cv_results.json (produced by code/04_train_model.py)
"""
from __future__ import annotations

import json
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, confusion_matrix

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger, log_operation
from utils.io import load_json, save_json, load_csv, load_pickle, ensure_dir

logger = get_logger("evaluate_model")


def ensure_file(path: Path) -> None:
    """Ensure the directory for a file exists."""
    ensure_dir(path.parent)


def isnan(val: Any) -> bool:
    """Check if a value is NaN."""
    if isinstance(val, float) and np.isnan(val):
        return True
    if isinstance(val, (list, np.ndarray)):
        return any(isnan(v) for v in val)
    return False


def load_eligible_subjects(path: Path) -> pd.DataFrame:
    """Load the eligible subjects CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {path}")
    df = load_csv(path)
    # Ensure subject_id column exists and is string
    if 'subject_id' not in df.columns:
        # Fallback if column name is different or missing
        # Try to infer from common BIDS naming or first column
        if len(df.columns) > 0:
            df = df.rename(columns={df.columns[0]: 'subject_id'})
        else:
            raise ValueError("Eligible subjects CSV is empty or has no columns")
    return df


def load_features(graph_metrics_path: Path, eligible_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load graph metrics and merge with eligible subjects to get features and labels.
    Assumes 'decline' column exists in eligible_subjects.csv or graph_metrics.csv.
    """
    # Load eligible subjects to get the ground truth labels
    eligible_df = load_eligible_subjects(eligible_path)
    
    # Load graph metrics
    if not graph_metrics_path.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {graph_metrics_path}")
    metrics_df = load_csv(graph_metrics_path)
    
    # Merge on subject_id
    if 'subject_id' not in metrics_df.columns:
        # Try common variations
        if 'id' in metrics_df.columns:
            metrics_df = metrics_df.rename(columns={'id': 'subject_id'})
        elif 'participant_id' in metrics_df.columns:
            metrics_df = metrics_df.rename(columns={'participant_id': 'subject_id'})
    
    if 'subject_id' not in eligible_df.columns:
        if 'id' in eligible_df.columns:
            eligible_df = eligible_df.rename(columns={'id': 'subject_id'})
        elif 'participant_id' in eligible_df.columns:
            eligible_df = eligible_df.rename(columns={'participant_id': 'subject_id'})

    merged = pd.merge(metrics_df, eligible_df[['subject_id', 'decline']], on='subject_id', how='inner')
    
    if merged.empty:
        raise ValueError("No matching subjects found between graph metrics and eligible subjects.")
    
    # Separate features and labels
    # Assume all columns except 'subject_id' and 'decline' are features
    feature_cols = [c for c in merged.columns if c not in ['subject_id', 'decline']]
    
    if not feature_cols:
        raise ValueError("No feature columns found in merged data.")
    
    X = merged[feature_cols]
    y = merged['decline']
    
    return X, y, merged['subject_id']


def split_features_labels(X: pd.DataFrame, y: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
    """Convert pandas DataFrame/Series to numpy arrays."""
    return X.values, y.values


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Calculate ROC-AUC, accuracy, and F1-score."""
    # Handle case where only one class is present (ROC-AUC undefined)
    if len(np.unique(y_true)) < 2:
        roc_auc = 0.0
    else:
        try:
            roc_auc = roc_auc_score(y_true, y_proba)
        except ValueError:
            roc_auc = 0.0
    
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    return {
        "roc_auc": float(roc_auc),
        "accuracy": float(acc),
        "f1_score": float(f1)
    }


def evaluate_model(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Evaluate a single model on full dataset (for final report).
    In the context of nested CV, we rely on cv_results.json for fold-wise metrics.
    This function is used to generate a 'final' evaluation if needed, 
    or to validate the model against the full dataset for the report.
    """
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else y_pred
    
    metrics = calculate_metrics(y, y_pred, y_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y, y_pred)
    
    return {
        "metrics": metrics,
        "confusion_matrix": cm.tolist(),
        "n_samples": int(len(y))
    }


def write_performance_report(report: Dict[str, Any], output_path: Path) -> None:
    """Write the performance report to JSON."""
    ensure_file(output_path)
    save_json(report, output_path)
    logger.log("write_performance_report", output=str(output_path), status="success")


def main() -> int:
    """
    Main entry point for model evaluation.
    Reads model, features, and labels. Calculates per-fold metrics from cv_results.json
    and computes overall statistics. Writes performance_report.json.
    """
    try:
        logger.log("evaluate_model_main", operation="start")

        # Define paths
        processed_dir = project_root / "data" / "processed"
        model_path = processed_dir / "model.pkl"
        graph_metrics_path = processed_dir / "graph_metrics.csv"
        eligible_path = processed_dir / "eligible_subjects.csv"
        cv_results_path = processed_dir / "cv_results.json"
        output_path = processed_dir / "performance_report.json"

        # Check dependencies
        for p in [model_path, graph_metrics_path, eligible_path, cv_results_path]:
            if not p.exists():
                logger.log("evaluate_model_main", operation="error", message=f"Missing required file: {p}")
                print(f"Error: Missing required file: {p}")
                return 1

        # Load CV results (contains per-fold metrics)
        cv_results = load_json(cv_results_path)
        
        if not cv_results or 'fold_results' not in cv_results:
            logger.log("evaluate_model_main", operation="error", message="cv_results.json missing 'fold_results'")
            print("Error: cv_results.json missing 'fold_results'")
            return 1

        fold_results = cv_results['fold_results']
        
        # Aggregate per-fold metrics
        metrics_list = []
        for fold_idx, fold_data in enumerate(fold_results):
            if 'metrics' in fold_data:
                metrics_list.append(fold_data['metrics'])
            else:
                # Fallback: calculate if metrics not stored but predictions are
                # (Assuming model was saved with predictions or we re-evaluate if possible)
                # For now, we rely on stored metrics. If missing, skip or error.
                logger.log("evaluate_model_main", operation="warning", message=f"Fold {fold_idx} missing metrics in cv_results")
                continue

        if not metrics_list:
            logger.log("evaluate_model_main", operation="error", message="No fold metrics found to aggregate")
            print("Error: No fold metrics found to aggregate")
            return 1

        # Calculate means and stds
        roc_aucs = [m['roc_auc'] for m in metrics_list if not isnan(m['roc_auc'])]
        accs = [m['accuracy'] for m in metrics_list if not isnan(m['accuracy'])]
        f1s = [m['f1_score'] for m in metrics_list if not isnan(m['f1_score'])]

        def safe_mean(lst):
            return float(np.mean(lst)) if lst else 0.0
        def safe_std(lst):
            return float(np.std(lst)) if lst else 0.0

        summary = {
            "roc_auc": {
                "mean": safe_mean(roc_aucs),
                "std": safe_std(roc_aucs),
                "values": roc_aucs
            },
            "accuracy": {
                "mean": safe_mean(accs),
                "std": safe_std(accs),
                "values": accs
            },
            "f1_score": {
                "mean": safe_mean(f1s),
                "std": safe_std(f1s),
                "values": f1s
            },
            "n_folds": len(metrics_list)
        }

        # Optional: Final evaluation on full dataset (if model is re-fitted on all data, 
        # which is not the case here as we used nested CV. 
        # However, the task asks for evaluation. We report the CV results as the primary metric.
        # If the model.pkl is the one from the best fold or re-trained on all, we could add it.
        # Given the pipeline structure, cv_results are the ground truth for performance.
        
        report = {
            "summary": summary,
            "fold_results": fold_results,
            "model_path": str(model_path),
            "status": "completed"
        }

        write_performance_report(report, output_path)
        logger.log("evaluate_model_main", operation="success", message=f"Report written to {output_path}")
        print(f"Performance report written to {output_path}")
        return 0

    except Exception as e:
        logger.log("evaluate_model_main", operation="error", error=str(e))
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())