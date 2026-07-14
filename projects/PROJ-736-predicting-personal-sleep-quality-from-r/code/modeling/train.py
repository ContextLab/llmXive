"""
Task T020: Implement training pipeline invocation and prediction saving.

This script:
1. Loads the preprocessed feature matrix and labels (from US1).
2. Invokes the NestedCVPipeline (T020a) to train ElasticNetCV with nested CV.
3. Logs Pearson r and R² per fold.
4. Saves outer-fold predictions to data/processed/predictions.npy.
"""
from __future__ import annotations

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, get_hyperparameter
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, get_logger
from utils.metrics import pearson_r, r_squared
from modeling.pipeline_factory import create_pipeline, NestedCVPipeline


def load_data():
    """
    Load feature matrix and labels from the US1 output.
    
    Expects:
      - data/processed/features.npy (or similar aggregated feature file)
      - data/processed/labels.npy (or extracted from behavioral CSV)
    
    Returns:
      X (np.ndarray): Shape (n_samples, n_features)
      y (np.ndarray): Shape (n_samples,)
      subject_ids (list): List of subject identifiers corresponding to rows.
    """
    paths = get_paths()
    logger = get_logger("train_data_loader")
    
    # Attempt to load from the standard US1 output location
    feature_path = paths["processed_features"]
    label_path = paths["processed_labels"]
    
    if not os.path.exists(feature_path):
        raise FileNotFoundError(f"Feature file not found at {feature_path}. "
                                "Run US1 pipeline first.")
    
    # Load features
    X = np.load(feature_path)
    
    # Load labels
    # If labels file exists, load it; otherwise try to derive from behavioral CSV
    if os.path.exists(label_path):
        y = np.load(label_path)
    else:
        # Fallback: try to load from behavioral CSV if it exists
        behavioral_path = paths["behavioral_csv"]
        if os.path.exists(behavioral_path):
            df = pd.read_csv(behavioral_path)
            # Assume column name 'SleepScore' or similar; adjust based on actual CSV
            # Based on HCP data, the column is often 'Sleep_Score' or 'Sleep_Quality'
            sleep_cols = [c for c in df.columns if 'sleep' in c.lower() or 'Sleep' in c]
            if not sleep_cols:
                raise ValueError("No sleep-related column found in behavioral CSV.")
            y = df[sleep_cols[0]].values
            # Filter y to match X if subject IDs are used for alignment
            # For simplicity in this implementation, we assume row order matches
            # In a robust system, we would align by Subject_ID
        else:
            raise FileNotFoundError(f"Label file not found at {label_path} "
                                    "and behavioral CSV not found at {behavioral_path}.")
    
    # Ensure shapes match
    if X.shape[0] != y.shape[0]:
        # Attempt alignment by subject ID if available
        # For now, raise error if mismatch
        raise ValueError(f"Feature matrix ({X.shape[0]} samples) and labels ({y.shape[0]} samples) "
                         f"mismatch in sample count.")
    
    # Load subject IDs if available (often stored in a separate file or inferred)
    # Assuming a file 'data/processed/subject_ids.npy' exists from US1
    subject_ids_path = paths.get("subject_ids", str(paths["data"] / "processed" / "subject_ids.npy"))
    if os.path.exists(subject_ids_path):
        subject_ids = np.load(subject_ids_path).tolist()
    else:
        # Fallback to generic IDs
        subject_ids = [f"sub_{i:04d}" for i in range(X.shape[0])]
    
    return X, y, subject_ids


def run_training(X, y, subject_ids):
    """
    Run the nested cross-validation pipeline.
    
    Args:
        X: Feature matrix
        y: Target vector
        subject_ids: List of subject IDs
    
    Returns:
        predictions: Outer-fold predictions (np.ndarray)
        metrics_log: List of dicts containing fold metrics
        model: The final trained pipeline (if applicable)
    """
    logger = get_logger("train_pipeline")
    
    # Get hyperparameters from config
    variance_threshold = get_hyperparameter("variance_threshold")
    pca_retention = get_hyperparameter("pca_retention")
    cv_folds = get_hyperparameter("cv_folds", 5)
    
    # Create the pipeline factory
    pipeline = create_pipeline(
        variance_threshold=variance_threshold,
        pca_retention=pca_retention,
        n_folds=cv_folds
    )
    
    # Execute nested CV
    # The pipeline_factory should handle the nested CV logic and return
    # outer-fold predictions and per-fold metrics
    try:
        result = pipeline.fit_predict(X, y)
        predictions = result["predictions"]
        fold_metrics = result["metrics"]
        best_model = result.get("best_model", None)
    except Exception as e:
        log_stage_error("training", f"Pipeline execution failed: {str(e)}")
        raise
    
    # Log per-fold metrics
    metrics_log = []
    for i, metrics in enumerate(fold_metrics):
        fold_id = f"Fold_{i+1}"
        r_val = metrics.get("pearson_r", 0.0)
        r2_val = metrics.get("r_squared", 0.0)
        metrics_log.append({
            "fold": fold_id,
            "pearson_r": float(r_val),
            "r_squared": float(r2_val)
        })
        logger.log(f"Fold_{i+1}_metrics", 
                   pearson_r=float(r_val), 
                   r_squared=float(r2_val))
    
    # Compute overall metrics on predictions
    overall_r = float(pearson_r(y, predictions))
    overall_r2 = float(r_squared(y, predictions))
    
    logger.log("overall_metrics", 
               pearson_r=overall_r, 
               r_squared=overall_r2)
    
    return predictions, metrics_log, best_model, overall_r, overall_r2


def save_predictions(predictions, subject_ids, output_path):
    """
    Save outer-fold predictions to disk.
    
    Args:
        predictions: np.ndarray of predictions
        subject_ids: list of subject IDs
        output_path: Path to save the .npy file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save as a structured array or separate files
    # The task specifies saving to data/processed/predictions.npy
    # We will save a dict containing predictions and subject_ids for clarity
    data_dict = {
        "predictions": predictions,
        "subject_ids": np.array(subject_ids)
    }
    np.save(output_path, data_dict, allow_pickle=True)
    log_stage_complete("save_predictions", message=f"Saved predictions to {output_path}")


def main():
    """Main entry point for T020."""
    logger = get_logger("main_train")
    log_stage_start("load_data", message="Reading feature matrix and labels")
    
    try:
        # 1. Load Data
        X, y, subject_ids = load_data()
        log_stage_complete("load_data", message=f"Loaded {X.shape[0]} samples")
        
        # 2. Run Training
        log_stage_start("Model Training", message="Running ElasticNetCV with nested CV")
        predictions, metrics_log, model, overall_r, overall_r2 = run_training(X, y, subject_ids)
        log_stage_complete("Model Training", message=f"Overall R={overall_r:.4f}, R²={overall_r2:.4f}")
        
        # 3. Save Predictions
        paths = get_paths()
        output_path = paths["predictions"]
        save_predictions(predictions, subject_ids, output_path)
        
        # 4. Save Metrics Log (optional, for debugging)
        metrics_log_path = str(paths["results"] / "train_metrics.json")
        with open(metrics_log_path, "w") as f:
            json.dump({
                "overall_pearson_r": overall_r,
                "overall_r_squared": overall_r2,
                "fold_metrics": metrics_log
            }, f, indent=2)
        
        print(f"Training complete. Predictions saved to {output_path}")
        return 0
        
    except Exception as e:
        log_stage_error("main", f"Execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
