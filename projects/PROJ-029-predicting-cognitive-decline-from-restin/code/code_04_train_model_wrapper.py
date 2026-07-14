"""Wrapper module to expose training functions from 04_train_model.py.

This module provides a clean interface to the training logic in 04_train_model.py
without importing the entire script's side effects.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Tuple, Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold, RFE

# Import utility functions from shared modules
from utils.stats import check_collinearity, filter_low_variance_features
from utils.logger import get_logger

logger = get_logger("train_model_wrapper")


def load_features_and_labels_from_disk(
    data_dir: Path,
    n_subjects: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Load features and labels from disk.

    Args:
        data_dir: Directory containing the data files
        n_subjects: Optional limit on number of subjects

    Returns:
        Tuple of (X, y) arrays
    """
    # Load graph metrics
    metrics_file = data_dir / "graph_metrics.csv"
    if not metrics_file.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {metrics_file}")

    df = pd.read_csv(metrics_file)

    # Load labels from eligible subjects file
    eligible_file = data_dir / "eligible_subjects.csv"
    if not eligible_file.exists():
        raise FileNotFoundError(f"Eligible subjects file not found: {eligible_file}")

    eligible_df = pd.read_csv(eligible_file)

    # Merge to get labels
    # Assume eligible_subjects.csv has columns: subject_id, decline_label
    # and graph_metrics.csv has columns: subject_id, metric1, metric2, ...

    merged = df.merge(eligible_df[["subject_id", "decline_label"]], on="subject_id", how="inner")

    if n_subjects is not None:
        merged = merged.head(n_subjects)

    # Extract features (all columns except subject_id and decline_label)
    feature_cols = [col for col in merged.columns if col not in ["subject_id", "decline_label"]]
    X = merged[feature_cols].values
    y = merged["decline_label"].values

    return X, y


def train_single_fold_model(
    X: np.ndarray,
    y: np.ndarray,
    random_state: int = 42
) -> float:
    """Train a model on the full dataset and return ROC-AUC.

    This is a simplified training function for use in permutation tests.
    It performs the same feature selection and model training as the main pipeline.

    Args:
        X: Feature matrix
        y: Labels
        random_state: Random seed

    Returns:
        ROC-AUC score
    """
    # Set random seed
    np.random.seed(random_state)

    # 1. Collinearity check (exclude features with correlation > 0.95)
    # Keep higher variance feature
    X_clean, selected_features = check_collinearity(X, threshold=0.95, keep_higher_variance=True)

    if X_clean.shape[1] == 0:
        logger.log("no_features_after_collinearity")
        return 0.5

    # 2. Variance thresholding (variance > 0.01)
    X_var, var_mask = filter_low_variance_features(X_clean, threshold=0.01)

    if X_var.shape[1] == 0:
        logger.log("no_features_after_variance")
        return 0.5

    # 3. RFE to select <= 20 features
    n_features = min(20, X_var.shape[1])
    if n_features <= 0:
        logger.log("no_features_after_rfe")
        return 0.5

    # Create a simple pipeline for RFE
    base_rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=1
    )

    # RFE
    rfe = RFE(estimator=base_rf, n_features_to_select=n_features, step=1)
    X_rfe = rfe.fit_transform(X_var, y)

    if X_rfe.shape[1] == 0:
        logger.log("no_features_after_rfe_final")
        return 0.5

    # 4. Train final model with best parameters (simplified: use fixed params)
    # In the full pipeline, these would come from grid search
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=random_state,
        n_jobs=1
    )

    model.fit(X_rfe, y)

    # Predict and calculate AUC
    # Use cross-validation to avoid overfitting in this estimation
    kfold = StratifiedKFold(n_splits=3, shuffle=True, random_state=random_state)
    auc_scores = []

    for train_idx, val_idx in kfold.split(X_rfe, y):
        X_train, X_val = X_rfe[train_idx], X_rfe[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        model.fit(X_train, y_train)
        y_pred_proba = model.predict_proba(X_val)[:, 1]

        # Handle case where all predictions are the same class
        try:
            auc = roc_auc_score(y_val, y_pred_proba)
        except ValueError:
            auc = 0.5

        auc_scores.append(auc)

    mean_auc = np.mean(auc_scores)
    logger.log("model_trained", auc=mean_auc, n_features=X_rfe.shape[1])

    return mean_auc
