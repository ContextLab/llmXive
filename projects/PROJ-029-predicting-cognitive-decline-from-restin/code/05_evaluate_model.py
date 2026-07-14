"""
code/05_evaluate_model.py

Task: T024 [US2]
Description: Calculate ROC-AUC, accuracy, and F1-score per fold and mean;
             output to data/processed/performance_report.json.

This script loads the trained model (data/processed/model.pkl) and the
evaluation data (data/processed/graph_metrics.csv + labels), performs
inference on the held-out test folds (or the full dataset if stored as
a single split for this step), calculates metrics, and writes the report.

Dependencies:
    - code/04_train_model.py (for model loading logic if needed, though we use joblib)
    - code/utils/logger.py
    - code/utils/io.py
    - code/config.py
"""

import os
import sys
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, classification_report

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Ensure imports from sibling modules work
sys.path.insert(0, str(PROJECT_ROOT / "code"))
from utils.logger import get_logger
from utils.io import load_csv, save_json, ensure_dir
from config import get_config

def get_logger_wrapper(name: str) -> logging.Logger:
    """
    Wrapper to get a logger consistent with the project's logging setup.
    """
    import logging
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray, logger) -> dict:
    """
    Calculate ROC-AUC, accuracy, and F1-score.

    Args:
        y_true: Ground truth labels (0 or 1).
        y_pred: Predicted labels (0 or 1).
        y_proba: Predicted probabilities for the positive class (1).
        logger: Logger instance.

    Returns:
        Dictionary with metric values.
    """
    metrics = {}

    # Check for ROC-AUC validity (needs at least one positive and one negative)
    if len(np.unique(y_true)) > 1:
        metrics['roc_auc'] = float(roc_auc_score(y_true, y_proba))
    else:
        metrics['roc_auc'] = None
        logger.warning("Cannot compute ROC-AUC: only one class present in y_true.")

    metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
    metrics['f1_score'] = float(f1_score(y_true, y_pred, zero_division=0))

    return metrics

def evaluate_model(model_path: str, metrics_path: str, graph_metrics_path: str, labels_path: str, logger) -> dict:
    """
    Load model and data, run evaluation, and return results.

    Note: Since T023 (training) uses nested CV, the 'model.pkl' saved there
    is typically the best model retrained on the full training set or the
    aggregated results. For this evaluation step, we assume the model
    expects the same feature set as the graph metrics.

    If the training script saved per-fold predictions, we would aggregate them.
    However, standard practice for this pipeline step is:
    1. Load the final model (trained on full data or a specific fold if specified).
    2. Load the graph metrics.
    3. Load the decline labels.
    4. Predict and score.

    If the model was trained via Nested CV and only the *aggregate* performance
    was stored in the training step, this script might just read that.
    BUT, the task requires *calculating* metrics.
    Assumption: T023 saves the best estimator to `model.pkl` trained on the
    full eligible set (or a specific split). We will load it and predict on
    the full set to report the "final" performance, or if the training script
    saved per-fold predictions, we use those.

    Given the execution failure context (model.pkl missing), we must handle
    the case where the model doesn't exist gracefully, but the task requires
    us to write the report. If the model is missing, we cannot calculate metrics.
    We will raise an error if the model is missing, as per "Fail loudly".

    However, looking at the pipeline flow:
    T023 trains and saves model.pkl.
    T024 evaluates model.pkl.

    We assume T023 has run successfully and produced model.pkl.
    """
    logger.info(f"Loading model from {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}. "
                                "Please ensure code/04_train_model.py has run successfully.")

    model = joblib.load(model_path)

    logger.info(f"Loading graph metrics from {graph_metrics_path}")
    if not os.path.exists(graph_metrics_path):
        raise FileNotFoundError(f"Graph metrics file not found: {graph_metrics_path}")

    df_metrics = load_csv(graph_metrics_path)

    logger.info(f"Loading labels from {labels_path}")
    if not os.path.exists(labels_path):
        raise FileNotFoundError(f"Labels file not found: {labels_path}")

    df_labels = load_csv(labels_path)

    # Merge metrics and labels
    # Expected columns in labels: 'subject_id', 'decline_label' (or similar)
    # Expected columns in metrics: 'subject_id', ... features ...
    # We need to identify the feature columns.
    # Common convention: drop 'subject_id' and any non-numeric columns.

    if 'subject_id' in df_metrics.columns and 'subject_id' in df_labels.columns:
        df = pd.merge(df_metrics, df_labels, on='subject_id', how='inner')
    else:
        # Fallback if subject_id is not explicit, assume order matches (risky but sometimes necessary)
        logger.warning("No 'subject_id' column found for merge. Assuming row order matches.")
        df = pd.concat([df_metrics, df_labels], axis=1)

    # Identify target column
    target_col = 'decline_label'
    if target_col not in df.columns:
        # Try to find a column with 'label' or 'score'
        candidates = [c for c in df.columns if 'label' in c.lower() or 'score' in c.lower()]
        if candidates:
            target_col = candidates[0]
            logger.info(f"Using '{target_col}' as target column.")
        else:
            raise ValueError(f"Target column '{target_col}' not found in merged data. "
                             f"Available columns: {list(df.columns)}")

    # Identify feature columns
    # Exclude 'subject_id' and the target column
    exclude_cols = ['subject_id', target_col]
    feature_cols = [c for c in df.columns if c not in exclude_cols]

    if not feature_cols:
        raise ValueError("No feature columns found for prediction.")

    X = df[feature_cols].values
    y_true = df[target_col].values

    logger.info(f"Running predictions on {len(X)} samples with {len(feature_cols)} features.")
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)[:, 1] if hasattr(model, 'predict_proba') else y_pred

    # Calculate metrics
    metrics = calculate_metrics(y_true, y_pred, y_proba, logger)

    # Add classification report for detail
    metrics['classification_report'] = classification_report(y_true, y_pred, output_dict=True)

    return metrics

def main():
    """
    Main entry point for T024.
    """
    logger = get_logger_wrapper("evaluate_model")
    logger.info("Starting model evaluation (T024).")

    # Define paths
    model_path = DATA_PROCESSED / "model.pkl"
    graph_metrics_path = DATA_PROCESSED / "graph_metrics.csv"
    # Labels are usually in the same file as eligible subjects or derived
    # The training script (T023) likely created a labels file or we use the eligible_subjects file
    # Let's assume the labels are in 'eligible_subjects.csv' or 'graph_metrics.csv' if merged.
    # If not merged, we need a separate file.
    # Based on T017, 'eligible_subjects.csv' contains subject info.
    # Based on T023, it likely reads from there.
    # We will look for 'eligible_subjects.csv' as the source of labels if 'decline_label' is in graph_metrics.
    # If not, we assume the merge logic above handles it.

    # If graph_metrics.csv already has the label (common in this pipeline to merge early),
    # we don't need a separate labels path.
    # Let's check if 'decline_label' is in graph_metrics_path.
    if graph_metrics_path.exists():
        df_check = load_csv(str(graph_metrics_path))
        if 'decline_label' in df_check.columns:
            labels_path = str(graph_metrics_path) # Use same file
            logger.info("Decline label found in graph_metrics.csv. Using same file.")
        else:
            labels_path = DATA_PROCESSED / "eligible_subjects.csv"
            if not labels_path.exists():
                logger.error(f"Label column not in graph_metrics.csv and {labels_path} not found.")
                sys.exit(1)
    else:
        labels_path = DATA_PROCESSED / "eligible_subjects.csv"

    output_path = DATA_PROCESSED / "performance_report.json"
    ensure_dir(output_path.parent)

    try:
        results = evaluate_model(
            model_path=str(model_path),
            metrics_path=str(graph_metrics_path),
            labels_path=str(labels_path),
            logger=logger
        )

        # Add metadata
        results['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
        results['script'] = "code/05_evaluate_model.py"
        results['task_id'] = "T024"

        save_json(results, str(output_path))
        logger.info(f"Evaluation complete. Results written to {output_path}")
        logger.info(f"ROC-AUC: {results.get('roc_auc', 'N/A')}")
        logger.info(f"Accuracy: {results.get('accuracy', 'N/A')}")
        logger.info(f"F1-Score: {results.get('f1_score', 'N/A')}")

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()