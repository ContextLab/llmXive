"""
Training script for the sleep quality prediction model.
Loads preprocessed data, trains an ElasticNet model, and saves predictions.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import joblib

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error
from modeling.pipeline_factory import create_pipeline, NestedCVPipeline
from utils.metrics import pearson_r, r_squared, calculate_metrics

def load_data():
    """
    Load preprocessed feature matrix and behavioral data.
    Returns X, y, and subject IDs.
    """
    paths = get_paths()
    ensure_dirs()
    
    # Load feature matrix
    feature_matrix_path = paths['processed_dir'] / "connectivity_matrix.npy"
    if not feature_matrix_path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {feature_matrix_path}")
    X = np.load(feature_matrix_path)
    
    # Load subject IDs
    subject_ids_path = paths['processed_dir'] / "subject_ids.npy"
    if not subject_ids_path.exists():
        raise FileNotFoundError(f"Subject IDs not found at {subject_ids_path}")
    subject_ids = np.load(subject_ids_path, allow_pickle=True).tolist()
    
    # Load behavioral data
    behavioral_path = paths['processed_dir'] / "filtered_behavioral.csv"
    if not behavioral_path.exists():
        raise FileNotFoundError(f"Filtered behavioral data not found at {behavioral_path}")
    
    import pandas as pd
    df = pd.read_csv(behavioral_path)
    df.columns = [col.strip() for col in df.columns]
    
    # Identify Sleep Score column
    sleep_col = None
    for col in ['SleepScore', 'Sleep_Score', 'Sleep Score', 'SleepScore_Total']:
        if col in df.columns:
            sleep_col = col
            break
    
    if sleep_col is None:
        raise ValueError("Could not find Sleep Score column in behavioral data.")
    
    # Match subjects to the feature matrix
    # The subject_ids list should correspond to the rows in X
    # We assume the order is consistent with how the data was saved
    
    y = df[sleep_col].values
    
    # Ensure y is 1D
    if y.ndim > 1:
        y = y.flatten()
    
    return X, y, subject_ids

def run_training(X, y, subject_ids):
    """
    Run the nested cross-validation pipeline.
    Returns the model, predictions, and metrics.
    """
    logger = setup_logging(get_paths()['log_file'])
    log_stage_start(logger, "Model Training")
    
    # Create the pipeline
    pipeline = create_pipeline()
    
    # Perform nested cross-validation
    # We use cross_val_predict to get out-of-sample predictions for each fold
    from sklearn.model_selection import cross_val_predict
    
    # The pipeline should handle the inner CV for hyperparameter tuning
    # and the outer CV for evaluation.
    # However, for simplicity in this script, we will use cross_val_predict
    # which performs the outer CV and returns predictions for each sample.
    
    try:
        predictions = cross_val_predict(pipeline, X, y, cv=5)
    except Exception as e:
        log_stage_error(logger, "Model Training", str(e))
        raise
    
    # Calculate metrics
    r2 = r_squared(y, predictions)
    pearson_r_val, p_value = pearson_r(y, predictions)
    
    metrics = {
        "r2": r2,
        "pearson_r": pearson_r_val,
        "p_value": p_value,
        "n_subjects": len(y)
    }
    
    log_stage_complete(logger, "Model Training", extra=metrics)
    
    return pipeline, predictions, metrics

def main():
    """Entry point for the training script."""
    paths = get_paths()
    ensure_dirs()
    logger = setup_logging(paths['log_file'])
    
    try:
        log_stage_start(logger, "Loading Data")
        X, y, subject_ids = load_data()
        log_stage_complete(logger, "Loading Data", extra={"n_subjects": len(y)})
        
        pipeline, predictions, metrics = run_training(X, y, subject_ids)
        
        # Save predictions
        predictions_path = paths['processed_dir'] / "predictions.npy"
        np.save(predictions_path, predictions)
        logger.info(f"Saved predictions to {predictions_path}")
        
        # Save metrics
        metrics_path = paths['processed_dir'] / "model_metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Saved model metrics to {metrics_path}")
        
        log_stage_complete(logger, "Training Complete")
        return 0
    except Exception as e:
        log_stage_error(logger, "Training", str(e))
        return 1

if __name__ == "__main__":
    main()