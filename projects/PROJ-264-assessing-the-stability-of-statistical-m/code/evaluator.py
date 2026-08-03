import logging
from typing import Any, Dict, Generator, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

from .preprocessor import create_preprocessing_pipeline
from .utils import set_seed

logger = logging.getLogger(__name__)

MODELS = {
    "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
    "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
    "LinearSVM": SVC(kernel="linear", random_state=42),
}

def evaluate_model_on_splits(
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    dataset_id: int,
) -> Dict[str, Any]:
    """
    Trains a model on a specific train/test split and calculates metrics.
    
    This function ensures leakage prevention by:
    1. Creating a fresh preprocessing pipeline for the training data only.
    2. Fitting the preprocessor on train data.
    3. Transforming both train and test data.
    4. Fitting the model on transformed train data.
    5. Predicting on transformed test data.
    6. Calculating Accuracy and F1 score on the test set.
    
    Args:
        X: Full feature array.
        y: Full target array.
        model_name: Key for the model in MODELS dict.
        train_idx: Indices for training set.
        test_idx: Indices for test set.
        dataset_id: OpenML ID for logging.
        
    Returns:
        Dictionary with model_name, dataset_id, accuracy, and f1_score.
    """
    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    
    # Split data
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Create preprocessing pipeline (Imputer + Scaler)
    # This ensures scaling parameters are fit ONLY on training data
    preprocessor = create_preprocessing_pipeline()
    
    # Fit preprocessor on training data only
    X_train_processed = preprocessor.fit_transform(X_train)
    
    # Transform test data using training statistics
    X_test_processed = preprocessor.transform(X_test)
    
    # Initialize and fit model
    model = MODELS[model_name]
    model.fit(X_train_processed, y_train)
    
    # Predict
    y_pred = model.predict(X_test_processed)
    
    # Calculate metrics INSIDE the loop on the hold-out fold
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    return {
        "dataset_id": dataset_id,
        "model_name": model_name,
        "accuracy": acc,
        "f1_score": f1,
    }

def run_repeated_stratified_cv(
    X: np.ndarray,
    y: np.ndarray,
    dataset_id: int,
    n_splits: int = 10,
    n_repeats: int = 10,
    random_state: int = 42,
) -> List[Dict[str, Any]]:
    """
    Runs repeated stratified k-fold cross-validation for all configured models.
    
    Args:
        X: Feature array.
        y: Target array.
        dataset_id: OpenML ID.
        n_splits: Number of folds.
        n_repeats: Number of repeats.
        random_state: Random seed.
        
    Returns:
        List of dictionaries containing metrics for every fold/repeat/model.
    """
    set_seed(random_state)
    
    results = []
    
    # Check sample size constraint
    n_samples = len(X)
    if n_samples < 100:
        logger.warning(f"Dataset {dataset_id} has {n_samples} samples (<100). Skipping.")
        return results
    
    logger.info(f"Starting Repeated Stratified CV for dataset {dataset_id} ({n_samples} samples)")
    
    cv = RepeatedStratifiedKFold(
        n_splits=n_splits, 
        n_repeats=n_repeats, 
        random_state=random_state
    )
    
    for repeat_idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
        for model_name in MODELS.keys():
            metrics = evaluate_model_on_splits(
                X=X,
                y=y,
                model_name=model_name,
                train_idx=train_idx,
                test_idx=test_idx,
                dataset_id=dataset_id,
            )
            metrics["fold_id"] = repeat_idx % n_splits + 1 # Simplified fold ID tracking per repeat
            metrics["repeat_id"] = repeat_idx + 1
            results.append(metrics)
            
    logger.info(f"Completed CV for dataset {dataset_id}. Generated {len(results)} records.")
    return results

def run_repeated_stratified_cv_corrected(
    X: np.ndarray,
    y: np.ndarray,
    dataset_id: int,
    n_splits: int = 10,
    n_repeats: int = 10,
    random_state: int = 42,
) -> List[Dict[str, Any]]:
    """
    Wrapper for run_repeated_stratified_cv to maintain API compatibility
    or for future corrected logic if needed.
    """
    return run_repeated_stratified_cv(
        X, y, dataset_id, n_splits, n_repeats, random_state
    )
