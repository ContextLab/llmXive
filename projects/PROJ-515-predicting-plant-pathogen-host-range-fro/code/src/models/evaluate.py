import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
from sklearn.metrics import roc_auc_score, precision_score, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from loguru import logger

from src.config import get_seed
from src.utils.logging import get_logger
from src.models.train import train_l1_logistic_regression, calculate_vif, run_vif_selection

# Initialize logger
logger = get_logger()

def calculate_auprc(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """
    Calculate Area Under the Precision-Recall Curve (AUPRC).
    
    Args:
        y_true: True binary labels (0 or 1).
        y_prob: Predicted probabilities for the positive class.
    
    Returns:
        AUPRC score.
    """
    if len(np.unique(y_true)) < 2:
        logger.warning("Only one class present in y_true. AUPRC is not defined.")
        return 0.0
    return roc_auc_score(y_true, y_prob, average='macro', multi_class='ovr')

def calculate_precision(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate precision score.
    
    Args:
        y_true: True binary labels.
        y_pred: Predicted binary labels.
    
    Returns:
        Precision score.
    """
    if len(np.unique(y_true)) < 2:
        return 0.0
    return precision_score(y_true, y_pred, zero_division=0)

def benjamini_hochberg_fdr(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
    
    Returns:
        List of adjusted p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array(p_values)[sorted_indices]
    
    adjusted_p_values = np.zeros(n)
    for i in range(n):
        adjusted_p_values[sorted_indices[i]] = sorted_p_values[i] * n / (i + 1)
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted_p_values[sorted_indices[i]] = min(adjusted_p_values[sorted_indices[i]], adjusted_p_values[sorted_indices[i + 1]])
    
    # Clip values to [0, 1]
    adjusted_p_values = np.clip(adjusted_p_values, 0, 1)
    
    return adjusted_p_values.tolist()

def cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
    
    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def run_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    seed: int = 42
) -> Tuple[float, float, List[float]]:
    """
    Run a permutation test to assess model significance.
    
    Args:
        X: Feature matrix.
        y: Labels.
        n_permutations: Number of permutations.
        seed: Random seed.
    
    Returns:
        Tuple of (observed_auprc, p_value, null_distribution).
    """
    rng = np.random.default_rng(seed)
    
    # Train model on original data
    model = LogisticRegression(penalty='l1', solver='liblinear', random_state=seed)
    model.fit(X, y)
    y_prob = model.predict_proba(X)[:, 1]
    observed_auprc = calculate_auprc(y, y_prob)
    
    null_distribution = []
    for i in range(n_permutations):
        y_shuffled = rng.permutation(y)
        model_perm = LogisticRegression(penalty='l1', solver='liblinear', random_state=seed)
        model_perm.fit(X, y_shuffled)
        y_prob_perm = model_perm.predict_proba(X)[:, 1]
        auprc_perm = calculate_auprc(y_shuffled, y_prob_perm)
        null_distribution.append(auprc_perm)
    
    # Calculate p-value
    p_value = np.sum(np.array(null_distribution) >= observed_auprc) / n_permutations
    
    return observed_auprc, p_value, null_distribution

def run_nested_cv_with_permutation(
    X: np.ndarray,
    y: np.ndarray,
    n_outer_folds: int = 5,
    n_inner_folds: int = 3,
    n_permutations: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run nested cross-validation with permutation testing.
    
    Args:
        X: Feature matrix.
        y: Labels.
        n_outer_folds: Number of outer CV folds.
        n_inner_folds: Number of inner CV folds.
        n_permutations: Number of permutations for significance testing.
        seed: Random seed.
    
    Returns:
        Dictionary with metrics and permutation results.
    """
    rng = np.random.default_rng(seed)
    outer_cv = KFold(n_splits=n_outer_folds, shuffle=True, random_state=seed)
    inner_cv = KFold(n_splits=n_inner_folds, shuffle=True, random_state=seed)
    
    auprc_scores = []
    precision_scores = []
    permutation_results = []
    
    for fold_idx, (outer_train_idx, outer_test_idx) in enumerate(outer_cv.split(X)):
        logger.info(f"Processing outer fold {fold_idx + 1}/{n_outer_folds}")
        
        X_outer_train, X_outer_test = X[outer_train_idx], X[outer_test_idx]
        y_outer_train, y_outer_test = y[outer_train_idx], y[outer_test_idx]
        
        # Inner loop for hyperparameter tuning
        best_score = -np.inf
        best_model = None
        
        for inner_train_idx, inner_val_idx in inner_cv.split(X_outer_train):
            X_inner_train, X_inner_val = X_outer_train[inner_train_idx], X_outer_train[inner_val_idx]
            y_inner_train, y_inner_val = y_outer_train[inner_train_idx], y_outer_train[inner_val_idx]
            
            # VIF selection on inner train
            vif_filtered_indices = run_vif_selection(X_inner_train, threshold=5.0)
            X_inner_train_vif = X_inner_train[:, vif_filtered_indices]
            X_inner_val_vif = X_inner_val[:, vif_filtered_indices]
            
            model = LogisticRegression(penalty='l1', solver='liblinear', random_state=seed)
            model.fit(X_inner_train_vif, y_inner_train)
            y_val_prob = model.predict_proba(X_inner_val_vif)[:, 1]
            score = calculate_auprc(y_inner_val, y_val_prob)
            
            if score > best_score:
                best_score = score
                best_model = model
                best_vif_indices = vif_filtered_indices
        
        # Apply VIF filtering to outer train and test
        X_outer_train_vif = X_outer_train[:, best_vif_indices]
        X_outer_test_vif = X_outer_test[:, best_vif_indices]
        
        # Train final model on outer train
        best_model.fit(X_outer_train_vif, y_outer_train)
        y_outer_test_prob = best_model.predict_proba(X_outer_test_vif)[:, 1]
        
        auprc = calculate_auprc(y_outer_test, y_outer_test_prob)
        y_outer_test_pred = best_model.predict(X_outer_test_vif)
        precision = calculate_precision(y_outer_test, y_outer_test_pred)
        
        auprc_scores.append(auprc)
        precision_scores.append(precision)
        
        # Permutation test on this fold
        obs_auprc, p_val, null_dist = run_permutation_test(
            X_outer_train_vif, y_outer_train, n_permutations=n_permutations, seed=seed
        )
        
        permutation_results.append({
            "fold": fold_idx,
            "observed_auprc": float(obs_auprc),
            "p_value": float(p_val),
            "null_distribution": [float(x) for x in null_dist]
        })
        
        logger.info(f"Fold {fold_idx + 1}: AUPRC={auprc:.4f}, Precision={precision:.4f}")
    
    return {
        "mean_auprc": float(np.mean(auprc_scores)),
        "std_auprc": float(np.std(auprc_scores)),
        "mean_precision": float(np.mean(precision_scores)),
        "std_precision": float(np.std(precision_scores)),
        "permutation_results": permutation_results
    }

def run_kfold_cv(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: int = 5,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run k-fold cross-validation and report AUPRC, precision, and calibrated probabilities.
    
    Args:
        X: Feature matrix (n_samples, n_features).
        y: Binary labels (n_samples,).
        n_folds: Number of CV folds.
        seed: Random seed for reproducibility.
    
    Returns:
        Dictionary containing:
            - mean_auprc: Average AUPRC across folds.
            - std_auprc: Standard deviation of AUPRC.
            - mean_precision: Average precision across folds.
            - std_precision: Standard deviation of precision.
            - fold_metrics: List of metrics for each fold.
            - calibrated_probabilities: Mean calibrated probabilities per sample (if applicable).
    """
    logger.info(f"Starting {n_folds}-fold cross-validation with seed {seed}")
    
    rng = np.random.default_rng(seed)
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=seed)
    
    auprc_scores = []
    precision_scores = []
    fold_metrics = []
    all_probs = np.zeros(len(y))
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(X)):
        logger.info(f"Processing fold {fold_idx + 1}/{n_folds}")
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # VIF selection on training fold
        vif_indices = run_vif_selection(X_train, threshold=5.0)
        if len(vif_indices) == 0:
            logger.warning(f"Fold {fold_idx + 1}: All features removed by VIF. Using original features.")
            vif_indices = list(range(X_train.shape[1]))
        
        X_train_vif = X_train[:, vif_indices]
        X_test_vif = X_test[:, vif_indices]
        
        # Train L1-regularized Logistic Regression
        model = LogisticRegression(penalty='l1', solver='liblinear', random_state=seed)
        model.fit(X_train_vif, y_train)
        
        # Predict probabilities
        y_prob = model.predict_proba(X_test_vif)[:, 1]
        y_pred = model.predict(X_test_vif)
        
        # Calculate metrics
        auprc = calculate_auprc(y_test, y_prob)
        precision = calculate_precision(y_test, y_pred)
        
        auprc_scores.append(auprc)
        precision_scores.append(precision)
        
        # Store calibrated probabilities (using Platt scaling / sigmoid is implicit in LogisticRegression)
        all_probs[test_idx] = y_prob
        
        fold_metrics.append({
            "fold": fold_idx + 1,
            "auprc": float(auprc),
            "precision": float(precision),
            "n_train_samples": int(len(y_train)),
            "n_test_samples": int(len(y_test)),
            "n_features_used": int(len(vif_indices))
        })
        
        logger.info(f"Fold {fold_idx + 1}: AUPRC={auprc:.4f}, Precision={precision:.4f}")
    
    result = {
        "mean_auprc": float(np.mean(auprc_scores)),
        "std_auprc": float(np.std(auprc_scores)),
        "mean_precision": float(np.mean(precision_scores)),
        "std_precision": float(np.std(precision_scores)),
        "fold_metrics": fold_metrics,
        "calibrated_probabilities": all_probs.tolist()
    }
    
    logger.info(f"Cross-validation complete. Mean AUPRC: {result['mean_auprc']:.4f} (+/- {result['std_auprc']:.4f})")
    return result

def print_summary(metrics: Dict[str, Any]) -> None:
    """
    Print a summary of the cross-validation results.
    
    Args:
        metrics: Dictionary returned by run_kfold_cv or run_nested_cv_with_permutation.
    """
    logger.info("=== Cross-Validation Summary ===")
    logger.info(f"Mean AUPRC: {metrics['mean_auprc']:.4f} (+/- {metrics['std_auprc']:.4f})")
    logger.info(f"Mean Precision: {metrics['mean_precision']:.4f} (+/- {metrics['std_precision']:.4f})")
    logger.info(f"Number of folds: {len(metrics['fold_metrics'])}")
    
    if 'permutation_results' in metrics:
        p_values = [r['p_value'] for r in metrics['permutation_results']]
        logger.info(f"Permutation Test p-values: {p_values}")

def main():
    """
    Main function to demonstrate k-fold cross-validation.
    This is intended to be called by the pipeline or for testing.
    """
    # Example usage (in a real scenario, load X and y from data files)
    logger.info("Running k-fold CV demonstration...")
    
    # Placeholder data for demonstration
    # In production, load from data/processed/features_matrix.csv and labels
    X_demo = np.random.rand(100, 10)
    y_demo = np.random.randint(0, 2, 100)
    
    metrics = run_kfold_cv(X_demo, y_demo, n_folds=5, seed=42)
    print_summary(metrics)

if __name__ == "__main__":
    main()
