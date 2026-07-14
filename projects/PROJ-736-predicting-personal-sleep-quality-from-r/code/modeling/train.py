"""Training script for sleep quality prediction model.

Implements nested cross-validation to train an ElasticNet model on
functional connectivity features, tuning hyperparameters within the
training folds, and saving out-of-fold predictions.
"""
from __future__ import annotations

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import log_stage_start, log_stage_complete, log_stage_error, setup_logging, get_logger
from config import get_paths, ensure_dirs
from modeling.pipeline_factory import create_pipeline, NestedCVPipeline
from utils.metrics import pearson_r, r_squared


def load_data(processed_dir: str, behavioral_file: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Load feature matrix and target vector from disk.
    
    Args:
        processed_dir: Directory containing processed feature vectors
        behavioral_file: Path to behavioral data CSV containing Sleep Scores
        
    Returns:
        Tuple of (X, y, subject_ids)
    """
    log_stage_start("Load Data", {"processed_dir": processed_dir, "behavioral": behavioral_file})
    
    # Load behavioral data to get Sleep Scores
    if not os.path.exists(behavioral_file):
        log_stage_error("Load Data", f"Behavioral file not found: {behavioral_file}")
        raise FileNotFoundError(f"Behavioral file not found: {behavioral_file}")
        
    df = pd.read_csv(behavioral_file)
    
    # Validate required columns
    if "Sleep Score" not in df.columns:
        log_stage_error("Load Data", "Missing 'Sleep Score' column in behavioral data")
        raise ValueError("Missing 'Sleep Score' column in behavioral data")
    if "Subject" not in df.columns:
        log_stage_error("Load Data", "Missing 'Subject' column in behavioral data")
        raise ValueError("Missing 'Subject' column in behavioral data")
        
    sleep_scores = df["Sleep Score"].values.astype(float)
    subject_ids = df["Subject"].astype(str).values.tolist()
    
    # Load feature vectors
    X_list = []
    valid_indices = []
    missing_count = 0
    
    features_dir = os.path.join(processed_dir, "features")
    if not os.path.exists(features_dir):
        log_stage_error("Load Data", f"Features directory not found: {features_dir}")
        raise FileNotFoundError(f"Features directory not found: {features_dir}")
        
    for i, sid in enumerate(subject_ids):
        feature_path = os.path.join(features_dir, f"{sid}_features.npy")
        if os.path.exists(feature_path):
            try:
                X_list.append(np.load(feature_path))
                valid_indices.append(i)
            except Exception as e:
                log_stage_error("Load Data", f"Failed to load {feature_path}: {str(e)}")
                missing_count += 1
        else:
            missing_count += 1
    
    if not X_list:
        log_stage_error("Load Data", "No valid feature files found")
        raise ValueError("No valid feature files found")
        
    X = np.vstack(X_list)
    y = sleep_scores[valid_indices]
    valid_ids = [subject_ids[i] for i in valid_indices]
    
    log_stage_complete("Load Data", {
        "X_shape": list(X.shape), 
        "y_shape": list(y.shape),
        "subjects_loaded": len(valid_ids),
        "subjects_missing": missing_count
    })
    return X, y, valid_ids


def run_training(X: np.ndarray, y: np.ndarray, subject_ids: List[str]) -> Dict[str, Any]:
    """Run nested cross-validation training with ElasticNet.
    
    Args:
        X: Feature matrix (subjects x edges)
        y: Target vector (Sleep Scores)
        subject_ids: List of subject IDs
        
    Returns:
        Dictionary containing model metrics, predictions, and metadata
    """
    log_stage_start("Training Pipeline", {
        "n_subjects": len(y),
        "n_features": X.shape[1] if len(X.shape) > 1 else 1
    })
    
    try:
        # Create the nested CV pipeline
        # This handles VarianceThreshold, PCA, and ElasticNetCV within folds
        pipeline = create_pipeline()
        
        # Run the nested cross-validation
        # The pipeline returns predictions for each sample from its held-out fold
        predictions, fold_metrics = pipeline.fit_and_predict(X, y)
        
        # Ensure predictions are numpy array
        predictions = np.array(predictions)
        
        # Calculate overall metrics
        overall_r = pearson_r(y, predictions)
        overall_r2 = r_squared(y, predictions)
        
        # Compile results
        results = {
            "pearson_r": float(overall_r),
            "r_squared": float(overall_r2),
            "predictions": predictions,
            "subject_ids": subject_ids,
            "y_true": y,
            "n_subjects": len(y),
            "n_features": X.shape[1],
            "fold_metrics": fold_metrics,
            "n_folds": len(fold_metrics) if fold_metrics else 0
        }
        
        log_stage_complete("Training Pipeline", {
            "pearson_r": float(overall_r),
            "r_squared": float(overall_r2),
            "n_subjects": len(y)
        })
        
        return results
        
    except Exception as e:
        log_stage_error("Training Pipeline", str(e))
        raise


def main() -> bool:
    """Main entry point for the training script."""
    # Setup logging
    paths = get_paths()
    log_dir = paths.get("logs", "data/logs")
    ensure_dirs([log_dir])
    log_file = os.path.join(log_dir, "pipeline_run.json")
    setup_logging(log_file)
    
    # Define paths
    processed_dir = paths.get("processed", "data/processed")
    behavioral_file = os.path.join(paths.get("raw", "data/raw"), "behavioral", "hcp1200_behavioral_data.csv")
    predictions_path = os.path.join(processed_dir, "predictions.npy")
    metrics_path = os.path.join(processed_dir, "training_metrics.json")
    
    try:
        # Ensure output directories exist
        ensure_dirs([processed_dir, os.path.dirname(predictions_path)])
        
        # Load data
        X, y, subject_ids = load_data(processed_dir, behavioral_file)
        
        # 2. Run Training
        log_stage_start("Model Training", message="Running ElasticNetCV with nested CV")
        predictions, metrics_log, model, overall_r, overall_r2 = run_training(X, y, subject_ids)
        log_stage_complete("Model Training", message=f"Overall R={overall_r:.4f}, R²={overall_r2:.4f}")
        
        # Save predictions to disk (required for T023)
        np.save(predictions_path, results["predictions"])
        log_stage_complete("Save Predictions", {"path": predictions_path})
        
        # Save metrics
        metrics_data = {
            "pearson_r": results["pearson_r"],
            "r_squared": results["r_squared"],
            "n_subjects": results["n_subjects"],
            "n_features": results["n_features"],
            "n_folds": results["n_folds"],
            "fold_metrics": results["fold_metrics"]
        }
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
        log_stage_complete("Save Metrics", {"path": metrics_path})
        
        return True
        
    except Exception as e:
        log_stage_error("main", f"Execution failed: {str(e)}")
        return 1



if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)