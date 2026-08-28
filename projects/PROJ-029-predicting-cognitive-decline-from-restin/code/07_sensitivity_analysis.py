"""
T030: Sensitivity Analysis (FR-006 & FR-012)

Part 1: Decision Threshold Sweep (FR-006)
- Sweeps classification thresholds around 0.50 on the baseline model.
- Reports FPR/FNR rates.

Part 2: Label Definition Sensitivity (FR-012)
- Retrains the model with different decline thresholds (2, 3, 4 points).
- Compares performance against the baseline (3-point) model.

Outputs:
- data/processed/decision_threshold_report.json
- data/processed/label_sensitivity_report.json
- data/processed/label_sensitivity_models/ (pkl files)
"""
from __future__ import annotations

import json
import os
import sys
import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve, confusion_matrix, accuracy_score, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from scipy.stats import pearsonr

# Project imports
from utils.logger import get_logger, log_operation
from utils.io import load_csv, save_json, ensure_dir
from config import get_config

logger = get_logger("sensitivity_analysis")

# Constants
BASELINE_THRESHOLD = 3  # Points drop for decline
LABEL_THRESHOLDS = [2, 3, 4]  # Points to test for FR-012
DECISION_THRESHOLDS = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]
RANDOM_SEED = 42

def load_baseline_model() -> Any:
    """Load the baseline model trained with 3-point threshold (from T023)."""
    model_path = Path("data/processed/model.pkl")
    if not model_path.exists():
        logger.log("error", message="Baseline model not found. Run T023 first.")
        sys.exit(1)
    
    with open(model_path, "rb") as f:
        return pickle.load(f)

def load_features_and_labels(threshold: int = BASELINE_THRESHOLD) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load graph metrics and reconstruct labels based on the specified threshold.
    This allows us to re-train for different label definitions (FR-012).
    """
    metrics_path = Path("data/processed/graph_metrics.csv")
    if not metrics_path.exists():
        logger.log("error", message="Graph metrics not found. Run T019 first.")
        sys.exit(1)
    
    df = load_csv(str(metrics_path))
    
    # We need to reconstruct the label based on the threshold.
    # Assuming the original data had 'mmse_baseline' and 'mmse_followup' or similar.
    # If the CSV only has the final label, we cannot re-train for different thresholds.
    # However, T019 outputs graph metrics. We need the raw scores to re-label.
    # Let's assume the raw scores are in a separate file or we need to re-derive.
    # Since T017a produced eligible_subjects.csv, let's check if we can load scores from there or a derived file.
    # Actually, the most robust way is if the graph metrics CSV includes the raw scores used for labeling.
    # If not, we must load the participants file again.
    
    # Attempt to load raw scores from eligible_subjects.csv if it contains them,
    # or re-load from data/raw/ds000246/participants.tsv if available.
    participants_path = Path("data/raw/ds000246/participants.tsv")
    
    if participants_path.exists():
        raw_df = pd.read_csv(participants_path, sep='\t')
        # Merge with graph metrics on subject_id
        # Note: This assumes subject_id format matches.
        df = df.merge(raw_df, on='subject_id', how='inner')
    else:
        # Fallback: If we can't find raw scores, we might be stuck.
        # But for the sake of the pipeline, we assume the graph_metrics.csv 
        # was augmented with the scores or we have access to them.
        # If the CSV has 'mmse_baseline' and 'mmse_followup', great.
        if 'mmse_baseline' not in df.columns or 'mmse_followup' not in df.columns:
            logger.log("error", message="Raw MMSE scores not found in graph_metrics.csv or participants.tsv. Cannot re-label.")
            sys.exit(1)

    # Create label based on threshold
    # Decline = baseline - followup >= threshold
    df['decline_label'] = (df['mmse_baseline'] - df['mmse_followup']) >= threshold
    df['decline_label'] = df['decline_label'].astype(int)

    # Select features (exclude subject_id and the label columns)
    feature_cols = [c for c in df.columns if c not in ['subject_id', 'mmse_baseline', 'mmse_followup', 'decline_label']]
    
    X = df[feature_cols].values
    y = df['decline_label'].values
    
    return X, y, feature_cols

def retrain_model_with_threshold(threshold: int, feature_cols: List[str]) -> Tuple[Any, Dict[str, float]]:
    """
    Retrain a Random Forest model with the specified label threshold.
    Returns the model and a metrics dict.
    """
    X, y, _ = load_features_and_labels(threshold)
    
    if len(X) == 0:
        logger.log("warning", message=f"No data for threshold {threshold}")
        return None, {}

    # Simple train/test split for evaluation of the re-trained model
    # In a real pipeline, we might use cross-validation, but for sensitivity
    # analysis on the label definition, a held-out set is sufficient to see
    # how the metric changes.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y if len(np.unique(y)) > 1 else None
    )

    # Use fixed parameters as per FR-003
    model = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=RANDOM_SEED)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_curve(y_test, y_proba)[2][-1]) if len(np.unique(y_test)) > 1 else 0.5
    }

    return model, metrics

@log_operation("decision_threshold_sweep")
def run_decision_threshold_sweep(model: Any, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    FR-006: Sweep decision thresholds around 0.50.
    """
    logger.log("info", message="Starting decision threshold sweep")
    
    if model is None or X is None or y is None:
        logger.log("error", message="Missing model or data for threshold sweep")
        return {}

    y_proba = model.predict_proba(X)[:, 1]
    
    results = []
    for thresh in DECISION_THRESHOLDS:
        y_pred = (y_proba >= thresh).astype(int)
        tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
        
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            "threshold": thresh,
            "fpr": fpr,
            "fnr": fnr,
            "tp": int(tp),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn)
        })

    logger.log("info", message=f"Decision threshold sweep complete. {len(results)} points evaluated.")
    return {"sweep_results": results}

@log_operation("label_definition_sensitivity")
def run_label_definition_sensitivity() -> Dict[str, Any]:
    """
    FR-012: Vary the decline definition threshold (2, 3, 4 points).
    Retrains models and compares performance.
    """
    logger.log("info", message="Starting label definition sensitivity analysis")
    
    baseline_metrics = None
    sensitivity_results = []
    
    # Load baseline model and data once to get feature columns
    baseline_model = load_baseline_model()
    X, y, feature_cols = load_features_and_labels(BASELINE_THRESHOLD)
    
    for thresh in LABEL_THRESHOLDS:
        logger.log("info", message=f"Training model with label threshold: {thresh}")
        
        model, metrics = retrain_model_with_threshold(thresh, feature_cols)
        
        if model is None:
            continue

        # Save model
        model_path = Path("data/processed/label_sensitivity_models")
        ensure_dir(str(model_path))
        with open(model_path / f"model_threshold_{thresh}.pkl", "wb") as f:
            pickle.dump(model, f)
        
        entry = {
            "label_threshold": thresh,
            "metrics": metrics,
            "model_path": f"model_threshold_{thresh}.pkl"
        }
        
        if thresh == BASELINE_THRESHOLD:
            baseline_metrics = metrics
            entry["is_baseline"] = True
        else:
            entry["is_baseline"] = False
            # Compare to baseline
            if baseline_metrics:
                entry["accuracy_delta"] = metrics["accuracy"] - baseline_metrics["accuracy"]
                entry["f1_delta"] = metrics["f1_score"] - baseline_metrics["f1_score"]
                entry["roc_auc_delta"] = metrics["roc_auc"] - baseline_metrics["roc_auc"]
        
        sensitivity_results.append(entry)

    logger.log("info", message="Label definition sensitivity analysis complete")
    return {"sensitivity_results": sensitivity_results, "baseline_threshold": BASELINE_THRESHOLD}

@log_operation("sensitivity_analysis_main")
def main() -> None:
    """Main entry point for T030."""
    logger.log("info", message="Starting Sensitivity Analysis (T030)")
    
    # --- Part 1: Decision Threshold Sweep (FR-006) ---
    logger.log("info", message="Part 1: Decision Threshold Sweep")
    baseline_model = load_baseline_model()
    X, y, _ = load_features_and_labels(BASELINE_THRESHOLD)
    
    threshold_report = run_decision_threshold_sweep(baseline_model, X, y)
    
    # Save Part 1 Output
    output_path_1 = Path("data/processed/decision_threshold_report.json")
    save_json(str(output_path_1), threshold_report)
    logger.log("info", message=f"Saved {output_path_1}")
    
    # --- Part 2: Label Definition Sensitivity (FR-012) ---
    logger.log("info", message="Part 2: Label Definition Sensitivity")
    label_report = run_label_definition_sensitivity()
    
    # Save Part 2 Output
    output_path_2 = Path("data/processed/label_sensitivity_report.json")
    save_json(str(output_path_2), label_report)
    logger.log("info", message=f"Saved {output_path_2}")
    
    logger.log("info", message="Sensitivity Analysis Complete")

if __name__ == "__main__":
    main()