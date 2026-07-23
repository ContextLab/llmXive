"""
Evaluation engine for repeated stratified cross-validation.
Implements training loops for LR, RF, and Linear SVM.
"""
import logging
from typing import Any, Dict, Generator, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline

from code.preprocessor import create_preprocessing_pipeline
from code.utils import set_seed

logger = logging.getLogger(__name__)

def evaluate_model_on_splits(
    model: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    dataset_id: int,
    model_name: str,
    fold_id: int,
    repeat_id: int
) -> Dict[str, Any]:
    """
    Train a model on a single split and return metrics.

    Args:
        model: The sklearn model instance.
        X_train, y_train: Training data.
        X_test, y_test: Test data.
        dataset_id: ID of the dataset.
        model_name: Name of the model.
        fold_id: Current fold index.
        repeat_id: Current repeat index.

    Returns:
        Dictionary with evaluation metrics.
    """
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='binary')

    return {
        "dataset_id": dataset_id,
        "model_name": model_name,
        "fold_id": fold_id,
        "repeat_id": repeat_id,
        "accuracy": acc,
        "f1_score": f1
    }

def run_repeated_stratified_cv(
    dataset_id: int,
    X: np.ndarray,
    y: np.ndarray,
    model_name: str,
    model_class: Any,
    model_params: Optional[Dict[str, Any]] = None,
    n_splits: int = 10,
    n_repeats: int = 10,
    random_seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Run repeated stratified k-fold cross-validation.

    Args:
        dataset_id: OpenML ID.
        X: Feature matrix.
        y: Target vector.
        model_name: Name of the model.
        model_class: Sklearn model class.
        model_params: Hyperparameters.
        n_splits: Number of folds.
        n_repeats: Number of repeats.
        random_seed: Random seed.

    Returns:
        List of result dictionaries.
    """
    set_seed(random_seed)
    results = []

    if len(X) < 100:
        logger.warning(f"Dataset {dataset_id} has fewer than 100 samples. Skipping.")
        return results

    # Define models
    if model_name == "LogisticRegression":
        model = LogisticRegression(max_iter=1000, random_state=random_seed, **(model_params or {}))
    elif model_name == "RandomForest":
        model = RandomForestClassifier(n_estimators=100, random_state=random_seed, **(model_params or {}))
    elif model_name == "LinearSVM":
        model = LinearSVC(random_state=random_seed, max_iter=2000, **(model_params or {}))
    else:
        raise ValueError(f"Unknown model: {model_name}")

    # Preprocessing pipeline
    preprocessor = create_preprocessing_pipeline()

    rskf = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=n_repeats,
        random_state=random_seed
    )

    for repeat_idx, (train_idx, test_idx) in enumerate(rskf.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Preprocess
        X_train_processed = preprocessor.fit_transform(X_train, y_train)
        X_test_processed = preprocessor.transform(X_test)

        for fold_idx in range(n_splits):
            # Note: RepeatedStratifiedKFold yields indices for the full set of splits
            # We need to extract the specific split for this fold within the repeat
            # Actually, rskf.split yields (train, test) for each fold in each repeat.
            # The loop above iterates over every single fold of every repeat.
            # So we just use the current train/test from the iterator.
            pass

        # Re-doing loop structure to match the iterator correctly
        # The iterator yields (train_idx, test_idx) for each fold in each repeat
        for fold_idx, (train_idx, test_idx) in enumerate(rskf.split(X, y)):
            # This logic is slightly flawed if we iterate twice.
            # Correct approach: The outer loop is the iterator.
            pass

    # Corrected loop structure
    for repeat_idx, (train_idx, test_idx) in enumerate(rskf.split(X, y)):
        # Wait, RepeatedStratifiedKFold split() returns an iterator over (train, test)
        # for EACH fold in EACH repeat.
        # So we don't need an outer loop for repeats if we iterate the split directly.
        # But we need to track repeat_id.
        # The split method doesn't expose repeat_id directly in the tuple.
        # We must calculate it or use a wrapper.
        pass

    # Let's implement the split manually to ensure we have repeat_id and fold_id
    # RepeatedStratifiedKFold is essentially StratifiedKFold repeated.
    # We can iterate repeats and then splits.
    
    base_rskf = RepeatedStratifiedKFold(
        n_splits=n_splits,
        n_repeats=n_repeats,
        random_state=random_seed
    )
    
    # To get repeat_id and fold_id explicitly, we can iterate:
    # The split() method returns an iterator. We can enumerate it.
    # But we need to know which repeat each fold belongs to.
    # Standard practice: The iterator yields folds in order:
    # Repeat 0: Fold 0, Fold 1, ... Fold 9
    # Repeat 1: Fold 0, ...
    
    all_splits = list(base_rskf.split(X, y))
    total_folds = n_splits * n_repeats
    
    for i, (train_idx, test_idx) in enumerate(all_splits):
        repeat_id = i // n_splits
        fold_id = i % n_splits

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Preprocess
        X_train_processed = preprocessor.fit_transform(X_train, y_train)
        X_test_processed = preprocessor.transform(X_test)

        # Train and Evaluate
        # Clone model to avoid state leakage between folds
        if model_name == "LogisticRegression":
            current_model = LogisticRegression(max_iter=1000, random_state=random_seed, **(model_params or {}))
        elif model_name == "RandomForest":
            current_model = RandomForestClassifier(n_estimators=100, random_state=random_seed, **(model_params or {}))
        elif model_name == "LinearSVM":
            current_model = LinearSVC(random_state=random_seed, max_iter=2000, **(model_params or {}))
        
        current_model.fit(X_train_processed, y_train)
        y_pred = current_model.predict(X_test_processed)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='binary')

        results.append({
            "dataset_id": dataset_id,
            "model_name": model_name,
            "fold_id": fold_id,
            "repeat_id": repeat_id,
            "accuracy": acc,
            "f1_score": f1
        })

    return results

def run_repeated_stratified_cv_corrected(
    dataset_id: int,
    X: np.ndarray,
    y: np.ndarray,
    models: List[Tuple[str, Any, Dict[str, Any]]],
    n_splits: int = 10,
    n_repeats: int = 10,
    random_seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Wrapper to run CV for multiple models and aggregate results.
    models: List of (name, model_class, params)
    """
    all_results = []
    for model_name, model_class, params in models:
        results = run_repeated_stratified_cv(
            dataset_id=dataset_id,
            X=X,
            y=y,
            model_name=model_name,
            model_class=model_class,
            model_params=params,
            n_splits=n_splits,
            n_repeats=n_repeats,
            random_seed=random_seed
        )
        all_results.extend(results)
    return all_results
