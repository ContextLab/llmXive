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

from config import get_paths, ensure_dirs, get_hyperparameter
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error
from utils.metrics import pearson_r, r_squared
from modeling.pipeline_factory import create_pipeline
from data.feature_engineering import load_feature_vectors
from data.download_hcp import load_behavioral_data, filter_subjects

def load_data():
    """
    Load feature vectors and behavioral data for subjects with valid Sleep Scores.
    Returns:
      X (np.ndarray): Feature matrix (subjects x features)
      y (np.ndarray): Target vector (Sleep Scores)
      subject_ids (list): List of subject IDs corresponding to rows in X and y
    """
    paths = get_paths()
    logger = logging.getLogger(__name__)

    log_stage_start("Data Loading")

    # Load behavioral data and filter for valid subjects
    behavioral_file = paths['behavioral_csv']
    if not os.path.exists(behavioral_file):
        raise FileNotFoundError(f"Behavioral data not found at {behavioral_file}. Run download_hcp.py first.")

    df = load_behavioral_data(behavioral_file)
    filtered_ids = filter_subjects(df)
    logger.info(f"Identified {len(filtered_ids)} valid subjects with Sleep Score data.")

    # Load feature vectors
    feature_dir = paths['processed_features']
    if not os.path.exists(feature_dir):
        raise FileNotFoundError(f"Feature directory not found at {feature_dir}. Run feature_engineering.py first.")

    X_list = []
    y_list = []
    id_list = []

    for subj_id in filtered_ids:
        feat_path = feature_dir / f"{subj_id}.npy"
        if feat_path.exists():
            feat_vec = np.load(feat_path)
            X_list.append(feat_vec)
            
            # Extract Sleep Score from behavioral dataframe
            row = df[df['Subject'] == subj_id]
            if not row.empty:
                sleep_score = row['Sleep Score'].values[0]
                if not np.isnan(sleep_score):
                    y_list.append(sleep_score)
                    id_list.append(subj_id)
            else:
                logger.warning(f"Subject {subj_id} in features but missing in behavioral data.")
        else:
            logger.warning(f"Feature file missing for subject {subj_id}")

    if len(X_list) == 0:
        raise ValueError("No valid feature vectors loaded. Check preprocessing pipeline.")

    X = np.vstack(X_list)
    y = np.array(y_list)
    
    log_stage_complete("Data Loading", details={"subjects": len(id_list), "features": X.shape[1]})
    return X, y, id_list

def run_training(X, y, subject_ids):
    """
    Run nested cross-validation with ElasticNetCV.
    Saves outer-fold predictions to data/processed/predictions.npy.
    """
    paths = get_paths()
    logger = logging.getLogger(__name__)
    
    log_stage_start("Model Training")

    # Ensure output directory exists
    ensure_dirs(paths['processed_dir'])

    # Create the pipeline using the factory (T020a)
    # T020a (pipeline_factory.py) encapsulates the nested CV logic
    pipeline = create_pipeline()

    # Perform cross-validation to get predictions for each sample
    # cross_val_predict returns predictions from the outer fold for each sample
    # This effectively simulates the nested CV structure if the pipeline itself handles inner CV
    
    # We need to ensure the pipeline handles the inner CV for hyperparameter tuning
    # The create_pipeline() function from T020a should return an ElasticNetCV wrapped in a Pipeline
    # which performs inner CV automatically when fit.
    
    # To get outer-fold predictions, we must manually split and predict if cross_val_predict 
    # doesn't respect the nested structure of the estimator itself.
    # However, ElasticNetCV performs internal CV. To get true nested CV predictions,
    # we need to wrap it or use cross_val_predict on the pipeline.
    # If the pipeline contains ElasticNetCV, cross_val_predict will use the internal CV
    # of ElasticNetCV for tuning, which acts as the inner loop.
    
    logger.info("Running nested cross-validation...")
    
    # Get predictions from outer folds
    # Note: If the pipeline's estimator (ElasticNetCV) does its own CV, 
    # cross_val_predict on the pipeline effectively implements nested CV 
    # provided we don't leak data.
    from sklearn.model_selection import KFold, cross_val_predict
    
    kf = KFold(n_splits=5, shuffle=True, random_state=get_hyperparameter('seed'))
    
    try:
        outer_predictions = cross_val_predict(pipeline, X, y, cv=kf)
    except Exception as e:
        log_stage_error("Model Training", str(e))
        raise

    # Calculate metrics per fold (approximate by calculating on the whole set of predictions vs true)
    # True nested CV metrics are usually aggregated from fold-specific models.
    # Here we calculate overall Pearson r and R2 on the outer predictions.
    pred_r = pearson_r(y, outer_predictions)
    pred_r2 = r_squared(y, outer_predictions)
    
    logger.info(f"Outer-fold Pearson r: {pred_r:.4f}")
    logger.info(f"Outer-fold R²: {pred_r2:.4f}")

    # Save predictions to the required path
    output_path = paths['processed_dir'] / "predictions.npy"
    np.save(output_path, outer_predictions)
    
    # Also save subject IDs to align predictions
    ids_path = paths['processed_dir'] / "prediction_subject_ids.npy"
    np.save(ids_path, np.array(subject_ids))

    log_stage_complete("Model Training", details={
        "output_file": str(output_path),
        "pearson_r": pred_r,
        "r_squared": pred_r2
    })

    return {
        "pearson_r": pred_r,
        "r_squared": pred_r2,
        "predictions_path": str(output_path)
    }

def main():
    """
    Main entry point for the training task (T020).
    """
    paths = get_paths()
    log_file = paths['log_dir'] / "pipeline_run.json"
    setup_logging(log_file)
    logger = logging.getLogger(__name__)

    logger.info("Starting Task T020: Model Training")

    try:
        # 1. Load Data
        X, y, subject_ids = load_data()
        logger.info(f"Loaded data: {X.shape[0]} subjects, {X.shape[1]} features")

        # 2. Run Training
        results = run_training(X, y, subject_ids)

        # 3. Log final results
        logger.info(f"Training complete. Results: {json.dumps(results)}")
        
        return 0

    except Exception as e:
        logger.error(f"Task T020 failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
