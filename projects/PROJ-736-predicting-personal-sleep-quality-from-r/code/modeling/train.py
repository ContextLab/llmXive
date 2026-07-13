import os
import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Any
from sklearn.linear_model import ElasticNetCV
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error

# Import from project API
from config import get_paths, ensure_dirs
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error, log_event
from data.feature_engineering import load_feature_vectors
from data.download_hcp import filter_subjects
from utils.metrics import pearson_r, r_squared as calc_r2

def load_data():
    """
    Load feature matrix and target (Sleep Score) from processed data.
    Returns X (n_samples, n_features), y (n_samples,), subject_ids (list)
    """
    log_stage_start("Data Loading", "Loading feature vectors and behavioral targets")
    paths = get_paths()
    behavioral_path = paths['raw_behavioral']
    
    if not os.path.exists(behavioral_path):
        log_stage_error("Data Loading", f"Behavioral data not found at {behavioral_path}")
        return None, None, []
    
    # Load behavioral data to get targets
    import pandas as pd
    try:
        df = pd.read_csv(behavioral_path)
        df.columns = df.columns.str.strip()
    except Exception as e:
        log_stage_error("Data Loading", f"Failed to parse behavioral CSV: {e}")
        return None, None, []
    
    # Find sleep score column
    sleep_col = None
    for col in df.columns:
        if 'Sleep' in col and 'Score' in col:
            sleep_col = col
            break
    
    if not sleep_col:
        # Fallback to first column if pattern not found, but log warning
        if len(df.columns) > 0:
            sleep_col = df.columns[0]
            log_event("Data Loading", f"Sleep score column not found by pattern, using fallback: {sleep_col}")
        else:
            log_stage_error("Data Loading", "No columns found in behavioral data")
            return None, None, []
    
    # Filter to valid subjects (same logic as preprocessing)
    valid_subjects = filter_subjects(behavioral_path)
    if not valid_subjects:
        log_stage_error("Data Loading", "No valid subjects found after filtering.")
        return None, None, []
    
    log_event("Data Loading", f"Found {len(valid_subjects)} valid subjects for training.")
    
    # Load features for valid subjects
    X, loaded_ids = load_feature_vectors(valid_subjects)
    
    if X is None or X.size == 0:
        log_stage_error("Data Loading", "No features loaded.")
        return None, None, []
    
    # Align targets
    # Create a map from subject_id (string) to sleep_score
    # Ensure subject IDs in df are strings for comparison
    id_to_score = {}
    for _, row in df.iterrows():
        sid = str(row['SubjectID'])
        if sid in valid_subjects:
            id_to_score[sid] = row[sleep_col]
    
    y = []
    final_ids = []
    
    for i, sid in enumerate(loaded_ids):
        if sid in id_to_score:
            y.append(id_to_score[sid])
            final_ids.append(sid)
        else:
            log_event("Data Loading", f"Subject {sid} in features but missing target, skipping.")
    
    if len(y) == 0:
        log_stage_error("Data Loading", "No matching subjects between features and targets.")
        return None, None, []
    
    y = np.array(y)
    X = np.array(X)
    
    log_stage_complete("Data Loading", f"Loaded {X.shape[0]} samples, {X.shape[1]} features.")
    return X, y, final_ids

def run_training(X: np.ndarray, y: np.ndarray, subject_ids: List[str]):
    """
    Run ElasticNet training with nested CV logic (outer loop for predictions, inner for tuning).
    Saves predictions to data/processed/predictions.npy
    Saves per-fold metrics to a JSON report.
    """
    log_stage_start("Training", "Starting ElasticNet training with nested CV")
    
    if X is None or X.size == 0:
        log_stage_error("Training", "No data provided for training.")
        return None, None
    
    n_samples = X.shape[0]
    if n_samples < 5:
        log_stage_error("Training", f"Insufficient samples ({n_samples}) for cross-validation.")
        return None, None
    
    # Configuration for CV
    n_splits = min(5, n_samples) # Ensure we don't split more than samples
    if n_splits < 2:
        n_splits = 2 # Minimum for split
    
    # Define alphas for grid search
    alphas = [0.01, 0.1, 1.0]
    
    # Outer CV loop for unbiased predictions
    kfold_outer = KFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    # We need to store predictions for each sample from the model trained on the rest
    outer_predictions = np.zeros(n_samples)
    fold_metrics = []
    
    log_event("Training", f"Starting outer CV with {n_splits} folds.")
    
    for fold_idx, (train_idx, test_idx) in enumerate(kfold_outer.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Inner pipeline: Scale -> ElasticNetCV
        # ElasticNetCV handles its own internal CV for alpha selection
        # We wrap it in a pipeline to ensure scaling is fit only on train data
        pipe = Pipeline([
            ('scaler', StandardScaler()),
            ('enet', ElasticNetCV(alphas=alphas, cv=3, random_state=42, max_iter=10000, n_jobs=-1))
        ])
        
        try:
            # Fit on training fold
            pipe.fit(X_train, y_train)
            
            # Predict on test fold (out-of-sample)
            y_pred = pipe.predict(X_test)
            
            # Store predictions in the correct positions
            outer_predictions[test_idx] = y_pred
            
            # Calculate metrics for this fold
            r = pearson_r(y_test, y_pred)
            r2 = calc_r2(y_test, y_pred)
            
            fold_metrics.append({
                "fold": fold_idx + 1,
                "pearson_r": float(r),
                "r_squared": float(r2),
                "n_train": len(train_idx),
                "n_test": len(test_idx),
                "best_alpha": float(pipe.named_steps['enet'].alpha_)
            })
            
            log_event("Training", f"Fold {fold_idx+1}: r={r:.4f}, R2={r2:.4f}, alpha={pipe.named_steps['enet'].alpha_}")
            
        except Exception as e:
            log_stage_error("Training", f"Error in fold {fold_idx}: {e}")
            # Continue to next fold if possible, or abort?
            # For robustness, we log and continue, but this fold's predictions remain 0
            continue
    
    # Aggregate metrics
    valid_metrics = [m for m in fold_metrics if m is not None]
    if not valid_metrics:
        log_stage_error("Training", "No successful folds completed.")
        return None, None
    
    avg_r = np.mean([m['pearson_r'] for m in valid_metrics])
    avg_r2 = np.mean([m['r_squared'] for m in valid_metrics])
    
    log_event("Training", f"Outer CV Complete. Avg Pearson r: {avg_r:.4f}, Avg R2: {avg_r2:.4f}")
    
    # Save outer-fold predictions
    paths = get_paths()
    # Ensure processed directory exists
    os.makedirs(paths['processed'], exist_ok=True)
    pred_path = os.path.join(paths['processed'], 'predictions.npy')
    np.save(pred_path, outer_predictions)
    log_stage_complete("Training", f"Predictions saved to {pred_path}")
    
    # Save model coefficients from the final model (trained on full data for interpretation)
    # Although the task asks for outer-fold predictions, we also want a final model for T029
    final_pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('enet', ElasticNetCV(alphas=alphas, cv=3, random_state=42, max_iter=10000, n_jobs=-1))
    ])
    final_pipe.fit(X, y)
    
    coef_path = os.path.join(paths['results'], 'model_coefs.npy')
    os.makedirs(os.path.dirname(coef_path), exist_ok=True)
    np.save(coef_path, final_pipe.named_steps['enet'].coef_)
    
    # Save fold metrics to a temporary JSON for the report generator to pick up later
    metrics_report = {
        "avg_pearson_r": float(avg_r),
        "avg_r_squared": float(avg_r2),
        "fold_metrics": valid_metrics,
        "n_samples": n_samples,
        "n_features": X.shape[1],
        "best_alpha_final": float(final_pipe.named_steps['enet'].alpha_)
    }
    
    metrics_path = os.path.join(paths['results'], 'training_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics_report, f, indent=2)
    log_stage_complete("Training", f"Metrics saved to {metrics_path}")
    
    return final_pipe.named_steps['enet'], outer_predictions

def main():
    """
    Main entry point for training.
    """
    paths = get_paths()
    ensure_dirs()
    
    X, y, subject_ids = load_data()
    
    if X is None:
        log_stage_error("Training", "Failed to load data. Aborting training.")
        sys.exit(1)
    
    model, predictions = run_training(X, y, subject_ids)
    
    if predictions is None:
        log_stage_error("Training", "Training failed to produce predictions.")
        sys.exit(1)
    
    log_stage_complete("Training", "Pipeline execution complete.")

if __name__ == "__main__":
    sys.exit(main())