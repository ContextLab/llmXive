"""
Model Training Module for Plant Disease Resistance Prediction.
Implements Random Forest with Stratified Cross-Validation and Hold-out Set Reservation.
"""
import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, GridSearchCV, train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.utils.constants import HOLD_OUT_FRACTION, RANDOM_STATE, DATA_PROCESSED_DIR
from code.utils.io import log_artifact, log_preprocessing_step

def train_model(data_path: str, labels_path: str, output_dir: str, random_state: int = RANDOM_STATE):
    """
    Train a Random Forest model with stratified cross-validation and hold-out reservation.
    
    FR-006: Reserve HOLD_OUT_FRACTION (0.20) of samples as independent hold-out set 
            BEFORE any feature selection or model training.
            
    FR-005: Train with Stratified 5-fold CV.
    
    Args:
        data_path: Path to CSV file containing metabolite features.
        labels_path: Path to CSV file containing resistance labels.
        output_dir: Directory to save model artifacts and metrics.
        random_state: Random seed for reproducibility.
        
    Returns:
        tuple: (model_path, metrics_path, cv_results_path)
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Log start
    log_preprocessing_step("Loading data for training", {"data_path": data_path, "labels_path": labels_path})
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    if not os.path.exists(labels_path):
        raise FileNotFoundError(f"Labels file not found: {labels_path}")
        
    X = pd.read_csv(data_path)
    # Handle case where labels might be in a different column name
    y_column = 'label' if 'label' in pd.read_csv(labels_path).columns else pd.read_csv(labels_path).columns[0]
    y = pd.read_csv(labels_path)[y_column].values
    
    n_samples = len(y)
    print(f"Total samples loaded: {n_samples}")
    
    if n_samples == 0:
        raise ValueError("No samples found in the input data.")
        
    # FR-006: Reserve hold-out set BEFORE any other processing
    # Ensure we have enough samples for stratification
    unique, counts = np.unique(y, return_counts=True)
    min_class_count = min(counts)
    if min_class_count < 2:
        raise ValueError("Insufficient samples per class for stratified split.")
        
    n_hold_out = int(n_samples * HOLD_OUT_FRACTION)
    if n_hold_out == 0:
        n_hold_out = 1 # Ensure at least one sample if dataset is tiny
        
    # Stratified split to preserve class distribution
    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X, y, test_size=HOLD_OUT_FRACTION, random_state=random_state, stratify=y
    )
    
    print(f"Training set size: {len(y_train)}")
    print(f"Hold-out set size: {len(y_holdout)}")
    
    # Define parameter grid for GridSearchCV
    # Task requires: n_estimators=500, max_depth=10, with GridSearchCV over max_depth [10, 15, 20]
    param_grid = {
        'n_estimators': [500],
        'max_depth': [10, 15, 20],
        'random_state': [random_state]
    }
    
    # Initialize Random Forest base estimator
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=10,
        random_state=random_state,
        n_jobs=-1
    )
    
    # FR-005: Stratified 5-fold CV
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    
    # GridSearchCV with the stratified splits
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=skf,
        scoring='balanced_accuracy',
        n_jobs=-1,
        verbose=1
    )
    
    # Fit on training data (hold-out is NOT touched here)
    print("Starting GridSearchCV on training data...")
    try:
        grid_search.fit(X_train, y_train)
    except Exception as e:
        raise RuntimeError(f"Model training failed: {str(e)}")
    
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best CV score: {grid_search.best_score_:.4f}")
    
    # Get the best model
    best_model = grid_search.best_estimator_
    
    # Evaluate on hold-out set (independent test)
    y_pred_holdout = best_model.predict(X_holdout)
    balanced_acc_holdout = balanced_accuracy_score(y_holdout, y_pred_holdout)
    
    print(f"Hold-out Balanced Accuracy: {balanced_acc_holdout:.4f}")
    
    # Prepare metrics
    metrics = {
        'best_params': grid_search.best_params_,
        'best_cv_score': float(grid_search.best_score_),
        'cv_scores': [float(score) for score in grid_search.cv_results_['mean_test_score']],
        'hold_out_size': len(y_holdout),
        'train_size': len(y_train),
        'hold_out_balanced_accuracy': float(balanced_acc_holdout),
        'random_state': random_state
    }
    
    # Save artifacts
    model_path = os.path.join(output_dir, "best_model.pkl")
    metrics_path = os.path.join(output_dir, "metrics.json")
    cv_results_path = os.path.join(output_dir, "cv_results.json")
    
    with open(model_path, 'wb') as f:
        pickle.dump(best_model, f)
        
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    with open(cv_results_path, 'w') as f:
        # Convert numpy types to native python types for JSON serialization
        cv_results_clean = {}
        for k, v in grid_search.cv_results_.items():
            if isinstance(v, np.ndarray):
                cv_results_clean[k] = v.tolist()
            else:
                cv_results_clean[k] = v
        json.dump(cv_results_clean, f, indent=2)
    
    # Log artifacts
    log_artifact("model", model_path)
    log_artifact("metrics", metrics_path)
    
    print(f"Model saved to {model_path}")
    print(f"Metrics saved to {metrics_path}")
    
    return model_path, metrics_path, cv_results_path

if __name__ == "__main__":
    # Example usage for local testing
    if len(sys.argv) < 4:
        print("Usage: python train.py <data_csv> <labels_csv> <output_dir>")
        sys.exit(1)
        
    data_file = sys.argv[1]
    labels_file = sys.argv[2]
    out_dir = sys.argv[3]
    
    train_model(data_file, labels_file, out_dir)