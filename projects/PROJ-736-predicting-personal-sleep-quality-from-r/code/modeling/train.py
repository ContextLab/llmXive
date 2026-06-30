"""
Training script for User Story 2 (Predictive Modeling).

Implements:
- Loading preprocessed features and labels
- Invoking the nested CV pipeline from pipeline_factory
- Tuning ElasticNetCV hyperparameters
- Computing per-fold Pearson r and R²
- Saving outer-fold predictions to data/processed/predictions.npy
"""
import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Project imports
from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, setup_logging
from utils.metrics import pearson_r, r_squared
from modeling.pipeline_factory import run_nested_cv_pipeline

def load_data() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load feature matrix X, target vector y, and subject IDs from processed data.
    
    Expects:
      - data/processed/features.npy: (N_subjects, N_features)
      - data/processed/labels.npy: (N_subjects,)
      - data/processed/subject_ids.npy: (N_subjects,)
    
    Returns:
      X, y, subject_ids
    """
    paths = get_paths()
    features_path = paths['processed_features']
    labels_path = paths['processed_labels']
    subject_ids_path = paths['processed_subject_ids']

    if not (features_path.exists() and labels_path.exists() and subject_ids_path.exists()):
        raise FileNotFoundError(
            f"Required processed data files not found. Ensure US1 pipeline has run. "
            f"Missing: {features_path.exists()}, {labels_path.exists()}, {subject_ids_path.exists()}"
        )

    X = np.load(features_path)
    y = np.load(labels_path)
    subject_ids = np.load(subject_ids_path, allow_pickle=True)

    # Validate shapes
    if X.shape[0] != y.shape[0] or X.shape[0] != len(subject_ids):
        raise ValueError("Dimension mismatch between features, labels, and subject IDs.")

    return X, y, subject_ids.tolist()

def run_training(log_handle) -> Dict[str, Any]:
    """
    Execute the full training pipeline:
    1. Load data
    2. Run nested CV with ElasticNetCV
    3. Compute metrics
    4. Save predictions
    
    Args:
        log_handle: Logger instance for structured logging
        
    Returns:
        Dictionary containing metrics and paths for ResultReport.json
    """
    log_stage_start(log_handle, "Training", "Starting model training on full dataset")
    
    try:
        # 1. Load Data
        log_stage_start(log_handle, "Data Loading", "Loading preprocessed features and labels")
        X, y, subject_ids = load_data()
        n_subjects = len(y)
        log_stage_complete(
            log_handle, 
            "Data Loading", 
            f"Loaded {n_subjects} subjects, {X.shape[1]} features"
        )

        # 2. Run Nested CV Pipeline
        log_stage_start(log_handle, "Model Training", "Executing nested cross-validation")
        
        results = run_nested_cv_pipeline(
            X=X,
            y=y,
            subject_ids=subject_ids,
            data_subset=None,  # Full dataset as per T020
            random_state=42,
            cv_outer=5,
            cv_inner=3
        )
        
        # results structure:
        # {
        #   'predictions': np.array (N,),
        #   'true_labels': np.array (N,),
        #   'outer_fold_metrics': [{'pearson_r': float, 'r_squared': float}, ...],
        #   'best_params': dict,
        #   'feature_importance': np.array (N_features,) (sum of absolute weights per feature across folds)
        # }

        outer_metrics = results['outer_fold_metrics']
        predictions = results['predictions']
        true_labels = results['true_labels']
        best_params = results['best_params']

        # 3. Compute Aggregate Metrics
        log_stage_start(log_handle, "Metrics Calculation", "Computing aggregate performance metrics")
        
        aggregate_pearson = pearson_r(true_labels, predictions)
        aggregate_r2 = r_squared(true_labels, predictions)
        
        log_stage_complete(
            log_handle,
            "Metrics Calculation",
            f"Aggregate Pearson r: {aggregate_pearson:.4f}, R²: {aggregate_r2:.4f}"
        )

        # 4. Save Predictions for T023
        paths = get_paths()
        ensure_dirs(paths['results'])
        predictions_path = paths['results'] / 'predictions.npy'
        
        log_stage_start(log_handle, "Output Saving", f"Saving predictions to {predictions_path}")
        np.save(predictions_path, predictions)
        log_stage_complete(log_handle, "Output Saving", "Predictions saved successfully")

        # 5. Prepare Report Data
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'dataset_size': n_subjects,
            'num_features': X.shape[1],
            'best_hyperparameters': best_params,
            'aggregate_metrics': {
                'pearson_r': float(aggregate_pearson),
                'r_squared': float(aggregate_r2)
            },
            'per_fold_metrics': [
                {
                    'fold': i + 1,
                    'pearson_r': float(m['pearson_r']),
                    'r_squared': float(m['r_squared'])
                }
                for i, m in enumerate(outer_metrics)
            ],
            'predictions_path': str(predictions_path.relative_to(paths['root'])),
            'status': 'completed'
        }

        log_stage_complete(log_handle, "Training", "Model training completed successfully")
        return report_data

    except Exception as e:
        log_stage_error(log_handle, "Training", str(e))
        raise

def main():
    """Entry point for the training script."""
    paths = get_paths()
    ensure_dirs(paths['logs'])
    
    # Setup logging
    log_path = paths['logs'] / 'pipeline_run.json'
    log_handle = setup_logging(log_path)
    
    try:
        report_data = run_training(log_handle)
        
        # Save a summary to console and log
        print(f"Training Complete. Aggregate R²: {report_data['aggregate_metrics']['r_squared']:.4f}")
        
    except Exception as e:
        print(f"Training Failed: {str(e)}")
        sys.exit(1)
    finally:
        # Flush logs
        for handler in log_handle.handlers:
            handler.flush()

if __name__ == "__main__":
    main()