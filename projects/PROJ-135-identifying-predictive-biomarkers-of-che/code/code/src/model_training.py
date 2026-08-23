"""
Model training module for biomarker discovery pipeline.
Handles Elastic-Net logistic regression with class imbalance handling.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.metrics import roc_auc_score, precision_recall_curve, balanced_accuracy_score
from sklearn.preprocessing import StandardScaler
from scipy.stats import ttest_rel

# Import from project modules
from code.src.config import get_project_root, ensure_directories
from code.src.utils import resource_monitor, check_limits

logger = logging.getLogger(__name__)

def load_training_data(tumor_type: str, gene_panel: List[str]) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load training data for a specific tumor type with fixed gene panel.

    Args:
        tumor_type: The tumor type identifier
        gene_panel: List of gene symbols to use as features

    Returns:
        Tuple of (feature matrix X, target vector y)
    """
    project_root = get_project_root()
    training_path = project_root / "data" / "processed" / f"{tumor_type}_training_vst.csv"

    if not training_path.exists():
        raise FileNotFoundError(f"Training data not found: {training_path}")

    df = pd.read_csv(training_path, index_col=0)

    # Filter to gene panel
    available_genes = [g for g in gene_panel if g in df.index]
    if len(available_genes) < len(gene_panel):
        logger.warning(f"Only {len(available_genes)}/{len(gene_panel)} genes available for {tumor_type}")

    X = df.loc[available_genes].T  # Transpose to samples x features
    X = X[available_genes].T

    # Load metadata for response labels
    metadata_path = project_root / "data" / "processed" / f"{tumor_type}_training_metadata.csv"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata not found: {metadata_path}")

    metadata = pd.read_csv(metadata_path, index_col=0)

    # Ensure sample order matches
    common_samples = X.index.intersection(metadata.index)
    X = X.loc[common_samples]
    metadata = metadata.loc[common_samples]

    if 'response_label' not in metadata.columns:
        raise ValueError(f"response_label column not found in metadata for {tumor_type}")

    y = metadata['response_label']

    # Convert to numeric (0/1)
    y = y.map({'responder': 1, 'non_responder': 0}).fillna(0)

    return X, y

def calculate_responder_ratio(y: pd.Series) -> float:
    """
    Calculate the ratio of responders in the target vector.

    Args:
        y: Target vector with response labels

    Returns:
        Ratio of responders (1s) to total samples
    """
    if len(y) == 0:
        return 0.0
    return y.mean()

def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    alpha: float = 0.1,
    l1_ratio: float = 0.5,
    max_iter: int = 1000,
    random_state: int = 42,
    force_class_weight: Optional[str] = None
) -> Tuple[LogisticRegression, Dict[str, Any]]:
    """
    Train an Elastic-Net logistic regression model with class imbalance handling.

    Args:
        X: Feature matrix (samples x features)
        y: Target vector
        alpha: Regularization strength
        l1_ratio: Mixing parameter for Elastic-Net (1 = L1, 0 = L2)
        max_iter: Maximum iterations
        random_state: Random seed
        force_class_weight: If 'balanced', force balanced class weights regardless of ratio

    Returns:
        Tuple of (trained model, metadata dict)
    """
    # Calculate responder ratio
    responder_ratio = calculate_responder_ratio(y)
    logger.info(f"Responder ratio: {responder_ratio:.3f}")

    # Determine class weights
    use_balanced = False
    if force_class_weight == 'balanced':
        use_balanced = True
        logger.info("Forcing balanced class weights")
    elif responder_ratio < 0.20:
        use_balanced = True
        logger.info(f"Responder ratio ({responder_ratio:.3f}) < 0.20, enabling balanced class weights")

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train model
    model = LogisticRegression(
        penalty='elasticnet',
        solver='saga',
        alpha=alpha,
        l1_ratio=l1_ratio,
        max_iter=max_iter,
        class_weight='balanced' if use_balanced else None,
        random_state=random_state
    )

    model.fit(X_scaled, y)

    # Calculate balanced accuracy
    y_pred = model.predict(X_scaled)
    bal_acc = balanced_accuracy_score(y, y_pred)

    metadata = {
        'alpha': alpha,
        'l1_ratio': l1_ratio,
        'responder_ratio': responder_ratio,
        'balanced_accuracy': bal_acc,
        'class_weight': 'balanced' if use_balanced else 'auto',
        'n_samples': len(y),
        'n_features': X.shape[1],
        'n_responders': int(y.sum()),
        'n_non_responders': int(len(y) - y.sum()),
    }

    return model, metadata

def nested_cv(
    X: pd.DataFrame,
    y: pd.Series,
    n_outer_folds: int = 5,
    n_inner_folds: int = 3,
    alpha_range: List[float] = [0.01, 0.1, 1.0],
    l1_ratio_range: List[float] = [0.2, 0.5, 0.8],
    random_state: int = 42
) -> Tuple[Dict[str, Any], List[float]]:
    """
    Perform nested cross-validation for hyperparameter optimization.

    Args:
        X: Feature matrix
        y: Target vector
        n_outer_folds: Number of outer CV folds
        n_inner_folds: Number of inner CV folds for hyperparameter tuning
        alpha_range: Range of alpha values to test
        l1_ratio_range: Range of l1_ratio values to test
        random_state: Random seed

    Returns:
        Tuple of (best parameters dict, list of outer fold AUC scores)
    """
    # Check resource limits
    error = check_limits()
    if error:
        raise error

    outer_cv = StratifiedKFold(n_splits=n_outer_folds, shuffle=True, random_state=random_state)
    outer_auc_scores = []

    best_params = None
    best_score = -np.inf

    for train_idx, test_idx in outer_cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        # Inner CV for hyperparameter tuning
        inner_cv = StratifiedKFold(n_splits=n_inner_folds, shuffle=True, random_state=random_state)
        inner_scores = []

        for alpha in alpha_range:
            for l1_ratio in l1_ratio_range:
                # Determine class weights based on training set
                responder_ratio = calculate_responder_ratio(y_train)
                class_weight = 'balanced' if responder_ratio < 0.20 else None

                model = LogisticRegression(
                    penalty='elasticnet',
                    solver='saga',
                    alpha=alpha,
                    l1_ratio=l1_ratio,
                    max_iter=1000,
                    class_weight=class_weight,
                    random_state=random_state
                )

                # Scale features
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)

                scores = cross_val_score(
                    model, X_train_scaled, y_train,
                    cv=inner_cv,
                    scoring='roc_auc'
                )
                mean_score = scores.mean()
                inner_scores.append({
                    'alpha': alpha,
                    'l1_ratio': l1_ratio,
                    'score': mean_score
                })

                if mean_score > best_score:
                    best_score = mean_score
                    best_params = {'alpha': alpha, 'l1_ratio': l1_ratio}

        # Train on full inner training set with best params
        if best_params:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)

            model = LogisticRegression(
                penalty='elasticnet',
                solver='saga',
                alpha=best_params['alpha'],
                l1_ratio=best_params['l1_ratio'],
                max_iter=1000,
                random_state=random_state
            )
            model.fit(X_train_scaled, y_train)

            # Evaluate on outer test set
            X_test_scaled = scaler.transform(X_test)
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            auc = roc_auc_score(y_test, y_pred_proba)
            outer_auc_scores.append(auc)

    return best_params, outer_auc_scores

def compute_metrics(
    model: LogisticRegression,
    X: pd.DataFrame,
    y: pd.Series,
    scaler: Optional[StandardScaler] = None
) -> Dict[str, Any]:
    """
    Compute comprehensive metrics for a trained model.

    Args:
        model: Trained LogisticRegression model
        X: Feature matrix
        y: Target vector
        scaler: Optional pre-fitted scaler

    Returns:
        Dictionary of metrics
    """
    if scaler is None:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    else:
        X_scaled = scaler.transform(X)

    y_pred_proba = model.predict_proba(X_scaled)[:, 1]
    y_pred = model.predict(X_scaled)

    auc = roc_auc_score(y, y_pred_proba)
    bal_acc = balanced_accuracy_score(y, y_pred)

    precision, recall, thresholds = precision_recall_curve(y, y_pred_proba)
    pr_auc = np.trapz(precision, recall)

    return {
        'roc_auc': auc,
        'balanced_accuracy': bal_acc,
        'precision_recall_auc': pr_auc,
        'n_samples': len(y),
        'n_responders': int(y.sum()),
        'n_non_responders': int(len(y) - y.sum()),
    }

def save_model(
    model: LogisticRegression,
    scaler: StandardScaler,
    metadata: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Save trained model and metadata to disk.

    Args:
        model: Trained model
        scaler: Fitted scaler
        metadata: Model metadata
        output_path: Path to save the model
    """
    ensure_directories([output_path.parent])

    model_data = {
        'model': model,
        'scaler': scaler,
        'metadata': metadata
    }

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    logger.info(f"Model saved to {output_path}")

def process_tumor_type(
    tumor_type: str,
    gene_panel: List[str],
    output_dir: Path,
    alpha: float = 0.1,
    l1_ratio: float = 0.5
) -> Dict[str, Any]:
    """
    Process a single tumor type: load data, train model, compute metrics.

    Args:
        tumor_type: Tumor type identifier
        gene_panel: List of gene symbols
        output_dir: Directory to save results
        alpha: Regularization strength
        l1_ratio: Elastic-net mixing parameter

    Returns:
        Dictionary of results
    """
    logger.info(f"Processing tumor type: {tumor_type}")

    # Load data
    X, y = load_training_data(tumor_type, gene_panel)

    # Check for class imbalance and handle
    responder_ratio = calculate_responder_ratio(y)
    force_weight = 'balanced' if responder_ratio < 0.20 else None

    # Train model
    model, train_metadata = train_model(
        X, y,
        alpha=alpha,
        l1_ratio=l1_ratio,
        force_class_weight=force_weight
    )

    # Compute metrics
    metrics = compute_metrics(model, X, y)

    # Merge metadata
    results = {**train_metadata, **metrics}

    # Save model
    model_path = output_dir / f"{tumor_type}_model.pkl"
    save_model(model, model.coef_, train_metadata, model_path)

    # Save metrics
    metrics_path = output_dir / f"{tumor_type}_cv_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Completed {tumor_type}: AUC={metrics['roc_auc']:.3f}, "
               f"BalAcc={metrics['balanced_accuracy']:.3f}, "
               f"ClassWeight={train_metadata['class_weight']}")

    return results

def main() -> None:
    """Main entry point for model training."""
    logging.basicConfig(level=logging.INFO)

    # Example usage (would be called from main pipeline)
    project_root = get_project_root()
    output_dir = project_root / "results" / "models"
    ensure_directories([output_dir])

    logger.info("Model training module ready")
    logger.info(f"Output directory: {output_dir}")

    # Note: Actual training would be triggered by the pipeline orchestrator
    # with real gene panel and tumor types

if __name__ == '__main__':
    main()