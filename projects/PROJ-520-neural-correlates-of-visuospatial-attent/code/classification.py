import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
import warnings

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.inspection import permutation_importance

from config import load_config, get_paths
from models import ClassifierResult, PermutationResult
from logging_config import get_pipeline_logger, log_stage_start, log_stage_end

logger = get_pipeline_logger(__name__)

def load_features(file_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load features and labels from the CSV produced by T023.
    Expects a CSV with a 'label' column and numeric feature columns.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature matrix not found at {file_path}. "
                                "Ensure T023 (feature extraction) has run successfully.")

    df = pd.read_csv(path)

    if 'label' not in df.columns:
        raise ValueError("Feature matrix must contain a 'label' column.")

    X = df.drop(columns=['label']).values
    y = df['label'].values

    # Basic sanity check
    if X.shape[0] != y.shape[0]:
        raise ValueError("Number of samples in X and y do not match.")

    logger.info(f"Loaded features: {X.shape[0]} epochs, {X.shape[1]} features.")
    return X, y

def train_and_validate(X: np.ndarray, y: np.ndarray, n_folds: int = 5, seed: int = 42) -> ClassifierResult:
    """
    Train an LDA classifier with 5-fold cross-validation.
    Returns a ClassifierResult object with accuracy, precision, recall metrics.
    """
    log_stage_start(logger, "Training LDA classifier with 5-fold CV")

    # Setup CV
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

    # Pipeline: Scaler -> LDA
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('lda', LDA())
    ])

    # Compute metrics
    scores_acc = cross_val_score(pipe, X, y, cv=cv, scoring='accuracy')
    
    # For precision/recall, we need to predict on each fold to aggregate
    # Using a loop to get per-fold predictions for robust metric calculation
    precisions = []
    recalls = []
    
    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        
        precisions.append(precision_score(y_test, y_pred, zero_division=0))
        recalls.append(recall_score(y_test, y_pred, zero_division=0))

    # Calculate means and stds
    acc_mean = float(np.mean(scores_acc))
    acc_std = float(np.std(scores_acc))
    prec_mean = float(np.mean(precisions))
    prec_std = float(np.std(precisions))
    rec_mean = float(np.mean(recalls))
    rec_std = float(np.std(recalls))

    result = ClassifierResult(
        accuracy_mean=acc_mean,
        accuracy_std=acc_std,
        precision_mean=prec_mean,
        precision_std=prec_std,
        recall_mean=rec_mean,
        recall_std=rec_std,
        n_folds=n_folds,
        model_type="LDA"
    )

    log_stage_end(logger, "LDA classification complete", {
        "accuracy": f"{acc_mean:.4f} (+/- {acc_std:.4f})",
        "precision": f"{prec_mean:.4f} (+/- {prec_std:.4f})",
        "recall": f"{rec_mean:.4f} (+/- {rec_std:.4f})"
    })

    return result

def permutation_test(X: np.ndarray, y: np.ndarray, n_permutations: int = 1000, 
                     cv: int = 5, seed: int = 42) -> PermutationResult:
    """
    Perform permutation testing to establish statistical significance.
    Returns a PermutationResult with p-value and null hypothesis decision.
    """
    log_stage_start(logger, f"Running permutation test ({n_permutations} iterations)")

    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('lda', LDA())
    ])

    # Actual score
    actual_scores = cross_val_score(pipe, X, y, cv=cv, scoring='accuracy')
    actual_mean = np.mean(actual_scores)

    # Permutation scores
    perm_scores = np.zeros(n_permutations)
    for i in range(n_permutations):
        # Shuffle labels
        y_perm = np.random.permutation(y)
        scores = cross_val_score(pipe, X, y_perm, cv=cv, scoring='accuracy')
        perm_scores[i] = np.mean(scores)
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation {i+1}/{n_permutations} complete")

    # Calculate p-value (one-sided: prob of perm_score >= actual_score)
    # If actual is better than chance, we look at tail
    p_value = (np.sum(perm_scores >= actual_mean) + 1) / (n_permutations + 1)
    
    # Null hypothesis rejection
    alpha = 0.05
    reject_null = p_value < alpha

    result = PermutationResult(
        actual_accuracy=actual_mean,
        permuted_scores=perm_scores,
        p_value=p_value,
        alpha=alpha,
        reject_null=reject_null,
        n_permutations=n_permutations
    )

    log_stage_end(logger, "Permutation test complete", {
        "p_value": p_value,
        "reject_null": reject_null,
        "actual_accuracy": actual_mean
    })

    return result

def run_classification(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main orchestration function for the classification task.
    Loads data, trains model, runs permutation test, and saves results.
    """
    paths = get_paths(config)
    features_path = paths['processed_features']
    output_results_path = paths['results_json']

    if not Path(features_path).exists():
        raise FileNotFoundError(f"Input features file missing: {features_path}. "
                                "Run T023 (feature extraction) first.")

    X, y = load_features(features_path)
    
    # Train and validate
    cv_result = train_and_validate(X, y, n_folds=5, seed=config.get('seed', 42))
    
    # Permutation test
    perm_result = permutation_test(X, y, n_permutations=1000, cv=5, seed=config.get('seed', 42))

    # Compile results
    results = {
        "classification_results": {
            "accuracy_mean": cv_result.accuracy_mean,
            "accuracy_std": cv_result.accuracy_std,
            "precision_mean": cv_result.precision_mean,
            "precision_std": cv_result.precision_std,
            "recall_mean": cv_result.recall_mean,
            "recall_std": cv_result.recall_std,
            "n_folds": cv_result.n_folds,
            "model_type": cv_result.model_type
        },
        "statistical_significance": {
            "permutation_p_value": perm_result.p_value,
            "actual_accuracy": perm_result.actual_accuracy,
            "n_permutations": perm_result.n_permutations,
            "alpha": perm_result.alpha,
            "reject_null_hypothesis": perm_result.reject_null
        }
    }

    # Ensure output directory exists
    Path(output_results_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_results_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Classification results saved to {output_results_path}")
    return results

def main():
    """Entry point for script execution."""
    config = load_config()
    try:
        results = run_classification(config)
        print(f"Classification Complete. P-value: {results['statistical_significance']['permutation_p_value']:.4f}")
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise

if __name__ == "__main__":
    main()