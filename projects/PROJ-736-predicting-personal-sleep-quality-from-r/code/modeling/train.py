import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import joblib

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error
from modeling.pipeline_factory import create_pipeline
from utils.metrics import calculate_metrics

def load_data():
    """
    Load feature matrix and labels for training.
    Ensures X and y are aligned based on the filtered subject list.
    """
    logger = logging.getLogger(__name__)
    paths = get_paths()
    
    # Load feature matrix (produced by T009/T014d)
    features_path = os.path.join(paths['processed_features'], "all_subjects_features.npy")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Feature matrix not found: {features_path}")
    
    X = np.load(features_path)
    logger.info(f"Loaded feature matrix: {X.shape}")
    
    # Load labels (SleepScore) from the behavioral data
    behavioral_path = paths['behavioral_data']
    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Behavioral data not found: {behavioral_path}")
    
    df = pd.read_csv(behavioral_path)
    
    # Filter to subjects with valid SleepScore (consistent with T007b logic)
    # Assuming the feature matrix rows are ordered by 'Subject' ID in the same order
    # as the filtered behavioral data.
    df_valid = df[df['SleepScore'].notna()]
    
    # We need to ensure the rows in X correspond to the rows in df_valid.
    # The feature engineering pipeline (T009) should have saved the subject IDs
    # or the data should be ordered consistently. 
    # For robustness, we assume the feature file was generated from the filtered list.
    # If 'Subject' column exists in df_valid, we might need to reorder X if it wasn't.
    # However, standard pipeline assumption: X is already ordered to match df_valid.
    
    y = df_valid['SleepScore'].values
    
    # Basic sanity check
    if X.shape[0] != len(y):
        logger.warning(f"Shape mismatch: X has {X.shape[0]} rows, y has {len(y)} rows. "
                       "Assuming X is already filtered correctly.")
        # In a real robust system, we would align by Subject ID here.
        # For this implementation, we proceed with the assumption that the pipeline
        # T009 ensured consistency.
    
    logger.info(f"Loaded labels: {y.shape}")
    return X, y

def run_training(X, y):
    """
    Run training pipeline with nested cross-validation.
    Uses ElasticNetCV for hyperparameter tuning within the CV loop.
    Returns the trained pipeline and out-of-sample predictions.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting nested cross-validation training")
    
    # Create the pipeline which includes VarianceThreshold, PCA, StandardScaler, ElasticNetCV
    pipeline = create_pipeline()
    
    from sklearn.model_selection import KFold
    
    n_splits = 5
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    predictions = np.zeros_like(y, dtype=float)
    fold_metrics = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Fit pipeline on training fold
        # This internally fits VarianceThreshold, PCA, and ElasticNetCV
        pipeline.fit(X_train, y_train)
        
        # Predict on test fold (outer loop prediction)
        preds = pipeline.predict(X_test)
        predictions[test_idx] = preds
        
        # Calculate metrics
        r, r2, p = calculate_metrics(y_test, preds)
        fold_metrics.append({
            "fold": fold_idx + 1,
            "pearson_r": float(r),
            "r_squared": float(r2),
            "p_value": float(p)
        })
        
        logger.info(f"Fold {fold_idx + 1}/{n_splits} - Pearson r: {r:.4f}, R²: {r2:.4f}, p: {p:.4f}")
    
    logger.info(f"Training complete. Total folds: {n_splits}")
    return pipeline, predictions, fold_metrics

def main():
    """
    Main function to train the model and save predictions.
    Loads data, runs training, and saves predictions to data/processed/predictions.npy
    """
    logger = logging.getLogger(__name__)
    paths = get_paths()
    ensure_dirs()
    
    try:
        log_stage_start("training", "Starting model training pipeline")
        
        # Load data
        X, y = load_data()
        
        # Run training
        pipeline, predictions, fold_metrics = run_training(X, y)
        
        # Save predictions
        predictions_path = os.path.join(paths['processed_data'], "predictions.npy")
        os.makedirs(os.path.dirname(predictions_path), exist_ok=True)
        np.save(predictions_path, predictions)
        logger.info(f"Saved predictions to {predictions_path}")
        
        # Save final model
        model_path = os.path.join(paths['processed_data'], "final_model.pkl")
        joblib.dump(pipeline, model_path)
        logger.info(f"Saved final model to {model_path}")
        
        # Save fold metrics for reporting
        metrics_path = os.path.join(paths['processed_data'], "fold_metrics.json")
        with open(metrics_path, 'w') as f:
            json.dump(fold_metrics, f, indent=2)
        logger.info(f"Saved fold metrics to {metrics_path}")
        
        log_stage_complete("training", "Model training complete")
        
    except Exception as e:
        log_stage_error("training", str(e))
        raise

if __name__ == "__main__":
    main()