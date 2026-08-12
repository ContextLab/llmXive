import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, train_test_split
from sklearn.metrics import balanced_accuracy_score
import logging

# Import from local utils
from code.utils.constants import HOLD_OUT_FRACTION, RANDOM_STATE, DATA_PROCESSED_DIR, RESULTS_DIR
from code.utils.io import compute_file_hash, log_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_model(X: pd.DataFrame, y: pd.Series) -> tuple:
    """
    Train a Random Forest model with Stratified 5-fold CV and GridSearchCV.
    
    This function implements the core training logic for US2:
    1. Splits data into train/hold-out using stratified sampling on binary_label BEFORE any feature selection.
    2. Trains Random Forest (n_estimators=500, max_depth=10) with Stratified k-fold CV.
    3. Performs GridSearchCV within the CV loop with param_grid={'max_depth': [low, medium, high]}.
    4. Saves the trained model and split indices to disk.
    
    Args:
        X (pd.DataFrame): Feature matrix (metabolite intensities)
        y (pd.Series): Binary resistance labels
        
    Returns:
        tuple: (best_model, best_params, X_hold, y_hold, train_indices, holdout_indices)
    """
    logger.info("Starting model training pipeline...")
    
    # Ensure directories exist
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Step 1: Split data into train/hold-out BEFORE any feature selection or scaling
    # This satisfies FR-006: independent hold-out set reserved before CV
    logger.info(f"Splitting data: {HOLD_OUT_FRACTION*100:.0f}% hold-out, {100 - HOLD_OUT_FRACTION*100:.0f}% training")
    X_temp, X_hold, y_temp, y_hold, train_indices, holdout_indices = train_test_split(
        X, y, 
        test_size=HOLD_OUT_FRACTION, 
        random_state=RANDOM_STATE, 
        stratify=y
    )
    
    logger.info(f"Training set size: {len(X_temp)}, Hold-out set size: {len(X_hold)}")
    logger.info(f"Train indices saved: {len(train_indices)}, Holdout indices saved: {len(holdout_indices)}")
    
    # Save split indices to disk (required artifact)
    split_indices_path = Path(DATA_PROCESSED_DIR) / "split_indices.json"
    split_data = {
        "train_indices": train_indices.tolist(),
        "holdout_indices": holdout_indices.tolist(),
        "random_state": RANDOM_STATE,
        "hold_out_fraction": HOLD_OUT_FRACTION
    }
    with open(split_indices_path, 'w') as f:
        json.dump(split_data, f, indent=2)
    logger.info(f"Saved split indices to {split_indices_path}")
    
    # Log the split artifact
    log_artifact(str(split_indices_path), "split_indices")
    
    # Step 2: Define the Random Forest model with fixed parameters from task spec
    # n_estimators=500, max_depth=10 (will be tuned via GridSearchCV)
    rf = RandomForestClassifier(
        random_state=RANDOM_STATE, 
        n_estimators=500, 
        max_depth=10,
        n_jobs=-1,
        class_weight='balanced'  # Handle potential class imbalance
    )
    
    # Step 3: Define parameter grid for GridSearchCV
    # Tuning max_depth over [10, 15, 20] as specified in task description
    param_grid = {
        'max_depth': [10, 15, 20],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }
    
    # Step 4: Set up Stratified k-fold CV
    cv = StratifiedKFold(
        n_splits=5, 
        shuffle=True, 
        random_state=RANDOM_STATE
    )
    
    # Step 5: Perform GridSearchCV within the CV loop
    logger.info("Starting GridSearchCV with 5-fold stratified CV...")
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=cv,
        scoring='balanced_accuracy',
        n_jobs=-1,
        verbose=1
    )
    
    # Fit on training data only (X_temp, y_temp)
    grid_search.fit(X_temp, y_temp)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    logger.info(f"Best parameters found: {best_params}")
    logger.info(f"Best CV balanced accuracy: {grid_search.best_score_:.4f}")
    
    # Step 6: Save the trained model to disk
    model_path = Path(DATA_PROCESSED_DIR) / "best_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(best_model, f)
    logger.info(f"Saved trained model to {model_path}")
    
    # Log the model artifact
    log_artifact(str(model_path), "best_model")
    
    # Compute and log training performance on the training set (for reference)
    y_train_pred = best_model.predict(X_temp)
    train_bal_acc = balanced_accuracy_score(y_temp, y_train_pred)
    logger.info(f"Training set balanced accuracy (post-hoc): {train_bal_acc:.4f}")
    
    # Compute hold-out performance (preliminary, will be formally evaluated in T021b)
    y_hold_pred = best_model.predict(X_hold)
    hold_bal_acc = balanced_accuracy_score(y_hold, y_hold_pred)
    logger.info(f"Hold-out set balanced accuracy (preliminary): {hold_bal_acc:.4f}")
    
    return best_model, best_params, X_hold, y_hold, train_indices, holdout_indices

def main():
    """
    Main entry point for training script.
    Loads preprocessed data from T017 and trains the model.
    """
    logger.info("=== Starting Model Training (T020) ===")
    
    # Load preprocessed data generated by T017
    matrix_path = Path(DATA_PROCESSED_DIR) / "batch_corrected_matrix.csv"
    labels_path = Path(DATA_PROCESSED_DIR) / "labels.csv"
    
    if not matrix_path.exists():
        raise FileNotFoundError(
            f"Preprocessed matrix not found at {matrix_path}. "
            "Please ensure T017 (generate_processed_outputs) has completed successfully."
        )
    
    if not labels_path.exists():
        raise FileNotFoundError(
            f"Labels file not found at {labels_path}. "
            "Please ensure T017 (generate_processed_outputs) has completed successfully."
        )
    
    logger.info(f"Loading data from {matrix_path} and {labels_path}")
    
    # Load feature matrix
    X = pd.read_csv(matrix_path, index_col=0)
    logger.info(f"Loaded feature matrix: {X.shape}")
    
    # Load labels
    labels_df = pd.read_csv(labels_path, index_col=0)
    
    # Ensure labels are binary and aligned with features
    if 'binary_label' not in labels_df.columns:
        raise ValueError(
            f"Labels file must contain 'binary_label' column. "
            f"Available columns: {list(labels_df.columns)}"
        )
    
    y = labels_df['binary_label']
    
    # Align indices between X and y
    common_indices = X.index.intersection(y.index)
    X = X.loc[common_indices]
    y = y.loc[common_indices]
    
    logger.info(f"Aligned data shape: {X.shape} samples, {X.shape[1]} features")
    
    if len(X) < 20:
        logger.warning(f"Small dataset size: {len(X)} samples. Training may be unstable.")
    
    # Train the model
    best_model, best_params, X_hold, y_hold, train_indices, holdout_indices = train_model(X, y)
    
    logger.info("=== Model Training Complete ===")
    logger.info(f"Best parameters: {best_params}")
    
    # Save preliminary metrics for immediate feedback
    preliminary_metrics = {
        "best_params": best_params,
        "hold_out_balanced_accuracy": balanced_accuracy_score(y_hold, best_model.predict(X_hold)),
        "training_samples": len(X_hold) + len(X_hold),  # Total samples
        "hold_out_samples": len(X_hold),
        "training_samples_used": len(X_hold)
    }
    
    metrics_path = Path(RESULTS_DIR) / "preliminary_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(preliminary_metrics, f, indent=2)
    logger.info(f"Saved preliminary metrics to {metrics_path}")
    
    return best_model, best_params

if __name__ == "__main__":
    main()