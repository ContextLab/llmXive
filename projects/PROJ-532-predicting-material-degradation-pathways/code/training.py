import os
import json
import logging
import pickle
from pathlib import Path
from typing import Tuple, Any, Dict

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, confusion_matrix, classification_report
from sklearn.preprocessing import MultiLabelBinarizer

# Local imports matching the provided API surface
from utils import setup_logging, ensure_dir, load_json, save_json
from ingestion import run_ingestion_pipeline
from preprocessing import run_preprocessing_pipeline
from evaluation import run_evaluation_pipeline

# Configure logger
logger = logging.getLogger(__name__)

def load_training_data(train_path: str) -> Tuple[pd.DataFrame, MultiLabelBinarizer, np.ndarray]:
    """
    Load the pre-split training dataset from parquet.
    
    Args:
        train_path: Path to the train_set.parquet file.
        
    Returns:
        Tuple of (features DataFrame, binarizer, label array)
    """
    logger.info(f"Loading training data from {train_path}")
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Training data file not found: {train_path}. "
                                "Ensure T019 (OOD Split) has been completed first.")
    
    df = pd.read_parquet(train_path)
    
    # Identify feature columns (all except 'labels')
    feature_cols = [col for col in df.columns if col != 'labels']
    X = df[feature_cols]
    
    # Handle multi-label format
    # The 'labels' column is expected to be a list of strings per row based on T019 output
    y_raw = df['labels'].apply(lambda x: x if isinstance(x, list) else [x])
    
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(y_raw)
    
    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features and {y.shape[1]} classes.")
    return X, mlb, y

def train_model(X: pd.DataFrame, y: np.ndarray, random_seed: int = 42) -> RandomForestClassifier:
    """
    Train a Random Forest multi-label classifier.
    
    Args:
        X: Feature matrix.
        y: Binary label matrix.
        random_seed: Random seed for reproducibility.
        
    Returns:
        Trained RandomForestClassifier instance.
    """
    logger.info("Training Random Forest model...")
    
    # Note: sklearn's RandomForestClassifier handles multi-output (multi-label) 
    # automatically when y is 2D (n_samples, n_classes)
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        random_state=random_seed,
        n_jobs=-1,
        verbose=1
    )
    
    model.fit(X, y)
    logger.info("Model training completed.")
    return model

def evaluate_model(model: RandomForestClassifier, X: pd.DataFrame, y: np.ndarray) -> Dict[str, Any]:
    """
    Evaluate the trained model on the provided data.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        y: True label matrix.
        
    Returns:
        Dictionary containing metrics (macro_f1, classification_report, confusion_matrix).
    """
    logger.info("Evaluating model...")
    y_pred = model.predict(X)
    
    macro_f1 = f1_score(y, y_pred, average='macro')
    report = classification_report(y, y_pred, output_dict=True, zero_division=0)
    
    # Confusion matrix per class (flattened for reporting or per-class)
    # Since it's multi-label, we calculate confusion matrix per class
    # For the report, we'll store the macro-averaged metrics and per-class details
    cm_per_class = []
    classes = model.classes_
    
    for i, cls in enumerate(classes):
        # Extract binary vector for this class
        y_true_cls = y[:, i]
        y_pred_cls = y_pred[:, i]
        cm = confusion_matrix(y_true_cls, y_pred_cls)
        cm_per_class.append({
            "class": cls,
            "matrix": cm.tolist()
        })
    
    return {
        "macro_f1": macro_f1,
        "classification_report": report,
        "confusion_matrices_per_class": cm_per_class,
        "y_pred_shape": list(y_pred.shape)
    }

def save_artifacts(
    model: RandomForestClassifier,
    metrics: Dict[str, Any],
    mlb: MultiLabelBinarizer,
    output_model_path: str,
    output_report_path: str
) -> None:
    """
    Save the trained model and metrics to disk.
    
    Args:
        model: Trained model.
        metrics: Evaluation metrics dictionary.
        mlb: MultiLabelBinarizer instance.
        output_model_path: Path to save the .pkl model artifact.
        output_report_path: Path to save the .json training report.
    """
    logger.info(f"Saving artifacts to {output_model_path} and {output_report_path}")
    
    # Ensure directories exist
    ensure_dir(Path(output_model_path))
    ensure_dir(Path(output_report_path))
    
    # Save model and binarizer together
    artifact_data = {
        "model": model,
        "mlb": mlb,
        "metrics": metrics
    }
    
    with open(output_model_path, 'wb') as f:
        pickle.dump(artifact_data, f)
    
    # Save metrics as JSON (handle non-serializable objects in metrics if any)
    # classification_report might contain numpy types, convert to native python
    def convert_types(obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_types(i) for i in obj]
        return obj
    
    serializable_metrics = convert_types(metrics)
    
    # Add metadata
    final_report = {
        "artifact_type": "ModelArtifact",
        "model_type": "RandomForestClassifier",
        "metrics": serializable_metrics,
        "classes": mlb.classes_.tolist(),
        "feature_names": list(model.feature_names_in_) if hasattr(model, 'feature_names_in_') else []
    }
    
    with open(output_report_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info("Artifacts saved successfully.")

def run_training_pipeline(
    train_data_path: str = "data/processed/train_set.parquet",
    output_model_path: str = "results/artifacts/model.pkl",
    output_report_path: str = "results/metrics/training_report.json",
    random_seed: int = 42
) -> Dict[str, Any]:
    """
    Run the full training pipeline: load, train, evaluate, save.
    
    Args:
        train_data_path: Path to the training parquet file.
        output_model_path: Path for the model artifact.
        output_report_path: Path for the training report.
        random_seed: Random seed.
        
    Returns:
        The metrics dictionary.
    """
    logger.info("Starting training pipeline...")
    
    # 1. Load Data
    X, mlb, y = load_training_data(train_data_path)
    
    # 2. Train Model
    model = train_model(X, y, random_seed)
    
    # 3. Evaluate Model (on training set for this task's scope, 
    #    though T024/025/026 usually handle test eval, T029 specifically asks 
    #    to save the artifact after training. We evaluate on the input 
    #    to get immediate metrics for the report).
    #    Note: In a strict flow, we might evaluate on the test set from T019,
    #    but T029 says "Save trained ModelArtifact". We'll evaluate on the 
    #    provided data to populate the report.
    metrics = evaluate_model(model, X, y)
    
    # 4. Save Artifacts
    save_artifacts(model, metrics, mlb, output_model_path, output_report_path)
    
    logger.info("Training pipeline completed successfully.")
    return metrics

def main():
    """Entry point for the training script."""
    setup_logging()
    
    # Paths relative to project root
    # These paths assume T019 has run and produced these files
    train_path = "data/processed/train_set.parquet"
    model_path = "results/artifacts/model.pkl"
    report_path = "results/metrics/training_report.json"
    
    try:
        metrics = run_training_pipeline(
            train_data_path=train_path,
            output_model_path=model_path,
            output_report_path=report_path
        )
        print(f"Training complete. Macro F1: {metrics['macro_f1']:.4f}")
        print(f"Model saved to: {model_path}")
        print(f"Report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
