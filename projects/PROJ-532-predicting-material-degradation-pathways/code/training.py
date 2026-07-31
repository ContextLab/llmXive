import os
import json
import logging
import pickle
from pathlib import Path
from typing import Tuple, Any, Dict

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import numpy as np

# Import shared utilities
from utils import setup_logging, save_json, ensure_dir, get_env_var
from config_env import configure_environment

# Configure environment and logging
configure_environment()
logger = setup_logging(__name__)

# Constants
TRAIN_DATA_PATH = Path("data/processed/train_set.parquet")
MODEL_ARTIFACT_PATH = Path("results/artifacts/model.pkl")
METRICS_REPORT_PATH = Path("results/metrics/training_report.json")
RANDOM_SEED = int(get_env_var("RANDOM_SEED", "42"))

def load_training_data() -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load the pre-split training data from parquet.
    Returns features (X), labels (y), and feature names.
    """
    if not TRAIN_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Training data not found at {TRAIN_DATA_PATH}. "
            "Please run T019 (preprocessing) to generate train_set.parquet."
        )

    df = pd.read_parquet(TRAIN_DATA_PATH)

    # Assume columns starting with 'feat_' are features, 'label_' are targets
    feature_cols = [c for c in df.columns if c.startswith("feat_")]
    label_cols = [c for c in df.columns if c.startswith("label_")]

    if not feature_cols or not label_cols:
        raise ValueError(
            f"Invalid training data format. Found {len(feature_cols)} features "
            f"and {len(label_cols)} labels. Expected at least one of each."
        )

    X = df[feature_cols].values
    y = df[label_cols].values

    logger.info(f"Loaded training data: {X.shape[0]} samples, {X.shape[1]} features, {y.shape[1]} labels")
    return df, X, y, feature_cols, label_cols

def train_model(X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    """
    Train a Random Forest classifier on CPU.
    Multi-label support is handled by sklearn's built-in MultiOutputClassifier logic
    (RandomForestClassifier handles multi-output natively for regression, but for classification
    with multi-output, sklearn usually requires MultiOutputClassifier wrapper.
    However, if y is 2D with multi-label, we need to handle it.
    Given the task is multi-label classification, we wrap RF in MultiOutputClassifier or
    ensure y is handled correctly.
    Standard RandomForestClassifier in sklearn expects 1D y for single-label.
    For multi-label, we use sklearn.multioutput.MultiOutputClassifier.
    """
    from sklearn.multioutput import MultiOutputClassifier

    logger.info("Training MultiOutput Random Forest model...")
    
    # Configure for CPU-only, deterministic results
    base_clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=RANDOM_SEED,
        n_jobs=1, # Force single thread for CPU-only constraint
        verbose=1
    )

    clf = MultiOutputClassifier(base_clf, n_jobs=1)
    clf.fit(X, y)

    logger.info("Model training completed.")
    return clf

def evaluate_model(clf: MultiOutputClassifier, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """
    Evaluate the model on the training set (or validation split if available,
    but T029 implies training report, so we evaluate on train for now or
    assume T028 generated the metrics).
    Since T028 is completed, we assume the metrics are calculated there.
    However, T029 asks to save the artifact and the report.
    We will re-calculate metrics on the training set to populate the report
    as a "Training Performance" snapshot, or load the results from T028 if they exist.
    
    Given the flow: T024 (Train) -> T025-T028 (Eval) -> T029 (Save).
    T028 generates the confusion matrix and metrics.
    We should load the results from T028's execution if possible, 
    or re-run the evaluation logic here to ensure the artifact is self-contained.
    
    To be safe and self-contained, we will perform the evaluation here using the
    functions from evaluation.py if they are available, or replicate the logic.
    Since evaluation.py is part of the API, we import from it.
    """
    from evaluation import calculate_macro_f1, generate_confusion_matrix

    y_pred = clf.predict(X)

    # Calculate Macro-F1
    macro_f1 = calculate_macro_f1(y, y_pred)

    # Generate confusion matrix (list of matrices for multi-label)
    conf_matrices = generate_confusion_matrix(y, y_pred)

    # Generate classification report per label
    report = {}
    feature_names = None # Will be passed if needed, but classification_report uses indices if no target_names
    
    for i in range(y.shape[1]):
        label_name = f"label_{i}"
        # Extract single column for sklearn report
        y_single = y[:, i]
        y_pred_single = y_pred[:, i]
        
        report[label_name] = classification_report(
            y_single, y_pred_single, output_dict=True
        )

    metrics = {
        "macro_f1": macro_f1,
        "confusion_matrices": conf_matrices,
        "classification_report": report,
        "model_params": clf[0].estimator[0].get_params(), # Accessing internal structure of MultiOutputClassifier
        "n_samples": X.shape[0],
        "n_features": X.shape[1],
        "n_labels": y.shape[1]
    }

    return metrics

def save_artifacts(model: Any, metrics: Dict[str, Any], feature_cols: list, label_cols: list) -> None:
    """
    Save the trained model and metrics to disk.
    """
    # Ensure directories exist
    ensure_dir(MODEL_ARTIFACT_PATH)
    ensure_dir(METRICS_REPORT_PATH)

    # Prepare model artifact dictionary
    artifact = {
        "model": model,
        "feature_names": feature_cols,
        "label_names": label_cols,
        "training_seed": RANDOM_SEED
    }

    # Save model pickle
    with open(MODEL_ARTIFACT_PATH, "wb") as f:
        pickle.dump(artifact, f)
    logger.info(f"Model artifact saved to {MODEL_ARTIFACT_PATH}")

    # Save metrics report
    # Convert numpy types to native Python for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return obj

    metrics_clean = json.loads(json.dumps(metrics, default=convert_numpy))
    save_json(METRICS_REPORT_PATH, metrics_clean)
    logger.info(f"Training report saved to {METRICS_REPORT_PATH}")

def run_training_pipeline() -> None:
    """
    Orchestrates the full training and evaluation pipeline.
    """
    logger.info("Starting training pipeline...")

    # 1. Load Data
    df, X, y, feature_cols, label_cols = load_training_data()

    # 2. Train Model
    model = train_model(X, y)

    # 3. Evaluate (Re-run evaluation to ensure report is current)
    # Note: T028 might have already run, but T029 needs to save the final state.
    # We trust the model state is the one from T024/T025/T026/T027/T028 flow.
    # If T028 produced a separate metrics file, we might merge, but T029
    # explicitly asks to save the report here.
    metrics = evaluate_model(model, X, y)

    # 4. Save Artifacts
    save_artifacts(model, metrics, feature_cols, label_cols)

    logger.info("Training pipeline completed successfully.")

def main():
    run_training_pipeline()

if __name__ == "__main__":
    main()
