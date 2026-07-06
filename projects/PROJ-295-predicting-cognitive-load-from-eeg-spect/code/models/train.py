import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error
import mne

def calculate_subject_split_size(
    n_subjects: int,
    test_size: float = 0.2,
    n_folds: int = 5
) -> int:
    """
    Calculate the dynamic subject split size for cross-validation.
    
    Args:
        n_subjects: Total number of subjects.
        test_size: Fraction of subjects for the test set.
        n_folds: Number of folds for cross-validation.
        
    Returns:
        Number of subjects per fold.
    """
    n_test = max(1, int(n_subjects * test_size))
    n_train = n_subjects - n_test
    
    # Ensure we have enough subjects for CV
    if n_train < n_folds:
        raise ValueError(f"Not enough subjects ({n_train}) for {n_folds}-fold cross-validation.")
    
    return n_train // n_folds

def subject_wise_cv(
    features: np.ndarray,
    labels: np.ndarray,
    subject_ids: np.ndarray,
    n_folds: int = 5,
    alpha: float = 1.0
) -> Tuple[List[Ridge], List[float], List[float]]:
    """
    Perform subject-wise 5-fold cross-validation.
    
    Args:
        features: Feature matrix (n_samples, n_features).
        labels: Target labels (n_samples,).
        subject_ids: Subject IDs for each sample.
        n_folds: Number of folds.
        alpha: Regularization strength for Ridge regression.
        
    Returns:
        Tuple of (models, r2_scores, rmse_scores).
    """
    gkf = GroupKFold(n_splits=n_folds)
    models = []
    r2_scores = []
    rmse_scores = []
    
    for train_idx, test_idx in gkf.split(features, labels, subject_ids):
        X_train, X_test = features[train_idx], features[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        
        # Train model
        model = Ridge(alpha=alpha)
        model.fit(X_train, y_train)
        models.append(model)
        
        # Evaluate
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
    
    return models, r2_scores, rmse_scores

def create_held_out_test_set(
    features: np.ndarray,
    labels: np.ndarray,
    subject_ids: np.ndarray,
    test_size: float = 0.2
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a distinct, non-overlapping held-out test set.
    
    Args:
        features: Feature matrix.
        labels: Target labels.
        subject_ids: Subject IDs.
        test_size: Fraction of subjects for the test set.
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test, test_subject_ids).
    """
    unique_subjects = np.unique(subject_ids)
    n_test = max(1, int(len(unique_subjects) * test_size))
    
    # Randomly select test subjects
    np.random.seed(42)  # For reproducibility
    test_subjects = np.random.choice(unique_subjects, size=n_test, replace=False)
    
    # Split data
    test_mask = np.isin(subject_ids, test_subjects)
    train_mask = ~test_mask
    
    X_train = features[train_mask]
    y_train = labels[train_mask]
    X_test = features[test_mask]
    y_test = labels[test_mask]
    test_subject_ids = subject_ids[test_mask]
    
    return X_train, y_train, X_test, y_test, test_subject_ids

def train_final_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    alpha: float = 1.0
) -> Ridge:
    """
    Train the final model on the training set.
    
    Args:
        X_train: Training features.
        y_train: Training labels.
        alpha: Regularization strength.
        
    Returns:
        Trained Ridge model.
    """
    model = Ridge(alpha=alpha)
    model.fit(X_train, y_train)
    return model

if __name__ == "__main__":
    print("Training module loaded successfully.")
