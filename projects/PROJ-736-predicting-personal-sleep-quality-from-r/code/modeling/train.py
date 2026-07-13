"""Training module for sleep quality prediction model.

Implements ElasticNetCV with nested cross-validation.
"""
from __future__ import annotations

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add parent directory to path
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, get_logger
from utils.metrics import pearson_r, r_squared
from modeling.pipeline_factory import create_pipeline

def load_data() -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load processed data for training.
    
    Returns:
        X: Feature matrix (n_subjects x n_features).
        y: Target vector (Sleep Scores).
        subject_ids: List of subject IDs.
    """
    paths = get_paths()
    processed_dir = Path(paths["processed_dir"])
    
    # Load filtered subjects
    filtered_path = processed_dir / "filtered_subjects.json"
    with open(filtered_path, 'r') as f:
        subjects = json.load(f)
    
    subject_ids = []
    features = []
    targets = []
    
    for subj in subjects:
        subj_id = subj['Subject']
        sleep_score = subj['Sleep_Score']
        
        # Load feature vector
        vec_file = processed_dir / f"{subj_id}_connectivity.npy"
        if not vec_file.exists():
            continue
        
        vec = np.load(vec_file)
        features.append(vec)
        targets.append(sleep_score)
        subject_ids.append(subj_id)
    
    if len(features) == 0:
        raise ValueError("No valid data loaded.")
    
    X = np.array(features)
    y = np.array(targets)
    
    return X, y, subject_ids

def run_training(X: np.ndarray, y: np.ndarray, subject_ids: List[str]) -> Dict:
    """
    Run the training pipeline with nested cross-validation.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        subject_ids: List of subject IDs.
    
    Returns:
        Dictionary containing model metrics and predictions.
    """
    # Create pipeline
    pipeline = create_pipeline()
    
    # Perform nested CV
    try:
        # Get predictions using cross_val_predict
        from sklearn.model_selection import cross_val_predict
        
        predictions = cross_val_predict(pipeline, X, y, cv=5)
        
        # Calculate metrics
        r2_score = r_squared(y, predictions)
        p_corr, _ = pearson_r(y, predictions)
        
        # Fit final model on full data
        pipeline.fit(X, y)
        
        # Extract coefficients
        coefficients = pipeline.named_steps['regressor'].coef_
        
        return {
            'predictions': predictions,
            'r2': r2_score,
            'pearson_r': p_corr,
            'coefficients': coefficients,
            'subject_ids': subject_ids
        }
        
    except Exception as e:
        log_stage_error("Training", str(e))
        return None

def main() -> bool:
    """Main entry point for training."""
    logger = get_logger()
    log_stage_start("Training")
    
    try:
        # Load data
        X, y, subject_ids = load_data()
        
        # Run training
        results = run_training(X, y, subject_ids)
        
        if results is None:
            raise RuntimeError("Training failed.")
        
        # Save predictions
        paths = get_paths()
        processed_dir = Path(paths["processed_dir"])
        
        predictions_file = processed_dir / "predictions.npy"
        np.save(predictions_file, results['predictions'])
        
        # Save model coefficients
        coef_file = processed_dir / "model_coefficients.npy"
        np.save(coef_file, results['coefficients'])
        
        # Save results metadata
        metadata = {
            'r2': float(results['r2']),
            'pearson_r': float(results['pearson_r']),
            'n_subjects': len(subject_ids),
            'n_features': len(results['coefficients'])
        }
        
        metadata_file = processed_dir / "training_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        log_stage_complete("Training")
        return True
        
    except Exception as e:
        log_stage_error("Training", str(e))
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
