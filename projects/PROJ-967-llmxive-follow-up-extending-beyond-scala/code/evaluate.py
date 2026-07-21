"""
evaluate.py - Metrics calculation and model evaluation for llmXive pipeline.

This module implements the evaluation logic for the Random Forest model trained
to predict fidelity loss based on entanglement features. It includes:
- Loading features and models
- Calculating R², MAE, and other metrics
- Performing permutation tests for significance
- Calculating null baseline (mean predictor) performance
- Saving results to JSON
"""

import argparse
import json
import logging
import sys
import pickle
import os
from typing import Dict, List, Tuple, Any

import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_features(path: str) -> List[Dict[str, Any]]:
    """
    Load features from a JSON file.

    Args:
        path: Path to the features JSON file.

    Returns:
        List of feature dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of features, got {type(data)}")

    logger.info(f"Loaded {len(data)} feature records from {path}")
    return data

def load_model(path: str):
    """
    Load a trained model from a pickle file.

    Args:
        path: Path to the model pickle file.

    Returns:
        The loaded model object.

    Raises:
        FileNotFoundError: If the file does not exist.
        pickle.PickleError: If the file cannot be loaded.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model file not found: {path}")

    with open(path, 'rb') as f:
        model = pickle.load(f)

    logger.info(f"Loaded model from {path}")
    return model

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate evaluation metrics: R² and MAE.

    Args:
        y_true: True target values.
        y_pred: Predicted target values.

    Returns:
        Dictionary with 'r2' and 'mae' keys.
    """
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    return {'r2': float(r2), 'mae': float(mae)}

def calculate_baseline_mae(y_true: np.ndarray) -> float:
    """
    Calculate the MAE of a null baseline (mean predictor).

    The null baseline predicts the mean of y_true for all samples.

    Args:
        y_true: True target values.

    Returns:
        MAE of the mean predictor.
    """
    mean_pred = np.full_like(y_true, fill_value=np.mean(y_true), dtype=float)
    return float(mean_absolute_error(y_true, mean_pred))

def perform_permutation_test(
    X: np.ndarray,
    y: np.ndarray,
    model_class,
    model_params: Dict[str, Any],
    n_permutations: int = 1000,
    random_state: int = 42
) -> Tuple[float, float]:
    """
    Perform a permutation test to assess the significance of the model's R².

    The test permutes the feature matrix X against the target y, trains the model
    on each permuted dataset, and calculates the R². The p-value is the fraction
    of permuted R² values that are >= the observed R².

    Args:
        X: Feature matrix (n_samples, n_features).
        y: Target vector (n_samples,).
        model_class: The sklearn model class to use (e.g., RandomForestRegressor).
        model_params: Parameters for the model.
        n_permutations: Number of permutations to perform.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (observed_r2, p_value).
    """
    logger.info(f"Starting permutation test with {n_permutations} permutations...")
    np.random.seed(random_state)

    # Train model on original data to get observed R²
    model = model_class(**model_params)
    model.fit(X, y)
    y_pred = model.predict(X)
    observed_r2 = r2_score(y, y_pred)
    logger.info(f"Observed R²: {observed_r2:.4f}")

    # Perform permutations
    permuted_r2s = []
    for i in range(n_permutations):
        # Permute X
        X_perm = X[np.random.permutation(len(X))]
        # Train and evaluate
        model_perm = model_class(**model_params)
        model_perm.fit(X_perm, y)
        y_pred_perm = model_perm.predict(X)
        r2_perm = r2_score(y, y_pred_perm)
        permuted_r2s.append(r2_perm)

        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")

    permuted_r2s = np.array(permuted_r2s)
    p_value = np.sum(permuted_r2s >= observed_r2) / n_permutations
    logger.info(f"Permutation test complete. P-value: {p_value:.4f}")

    return observed_r2, float(p_value)

def evaluate_model(
    X: np.ndarray,
    y: np.ndarray,
    model,
    n_folds: int = 5,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Evaluate a trained model using k-fold cross-validation.

    Args:
        X: Feature matrix.
        y: Target vector.
        model: Trained model object.
        n_folds: Number of CV folds.
        random_state: Random seed.

    Returns:
        Dictionary with CV metrics (mean R², std R²).
    """
    logger.info(f"Running {n_folds}-fold cross-validation...")
    kfold = KFold(n_splits=n_folds, shuffle=True, random_state=random_state)

    cv_scores = cross_val_score(model, X, y, cv=kfold, scoring='r2')
    mean_r2 = float(np.mean(cv_scores))
    std_r2 = float(np.std(cv_scores))

    logger.info(f"CV R²: {mean_r2:.4f} ± {std_r2:.4f}")

    return {
        'mean_r2': mean_r2,
        'std_r2': std_r2,
        'cv_scores': cv_scores.tolist()
    }

def save_results(results: Dict[str, Any], path: str) -> None:
    """
    Save evaluation results to a JSON file.

    Args:
        results: Dictionary of results to save.
        path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Evaluate model performance')
    parser.add_argument(
        '--features',
        type=str,
        default='data/processed/features.json',
        help='Path to features JSON file'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='results/model.pkl',
        help='Path to model pickle file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/results.json',
        help='Path to output results JSON file'
    )
    parser.add_argument(
        '--n-permutations',
        type=int,
        default=1000,
        help='Number of permutations for significance test'
    )
    parser.add_argument(
        '--n-folds',
        type=int,
        default=5,
        help='Number of CV folds'
    )
    parser.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Random seed'
    )
    return parser.parse_args()

def main():
    """Main entry point for evaluation."""
    args = parse_args()

    # Load features
    try:
        features = load_features(args.features)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to load features: {e}")
        sys.exit(1)

    if len(features) == 0:
        logger.error("No features found. Cannot evaluate.")
        sys.exit(1)

    # Extract X and y
    # Expected keys: 'sample_id', 'variance', 'entropy', 'dominant_eigenvalue', 'fidelity_loss'
    required_features = ['variance', 'entropy', 'dominant_eigenvalue']
    target = 'fidelity_loss'

    # Validate all samples have required keys
    for i, sample in enumerate(features):
        for key in required_features + [target]:
            if key not in sample:
                logger.error(f"Sample {i} missing required key: {key}")
                sys.exit(1)

    X = np.array([[s[k] for k in required_features] for s in features])
    y = np.array([s[target] for s in features])

    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Target vector shape: {y.shape}")

    # Load model
    try:
        model = load_model(args.model)
    except (FileNotFoundError, pickle.PickleError) as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # Calculate baseline MAE
    baseline_mae = calculate_baseline_mae(y)
    logger.info(f"Null baseline MAE: {baseline_mae:.4f}")

    # Evaluate model with CV
    cv_results = evaluate_model(X, y, model, n_folds=args.n_folds, random_state=args.random_state)

    # Perform permutation test
    observed_r2, p_value = perform_permutation_test(
        X, y, RandomForestRegressor,
        model_params={
            'n_estimators': 100,
            'max_depth': None,
            'random_state': args.random_state,
            'n_jobs': 2
        },
        n_permutations=args.n_permutations,
        random_state=args.random_state
    )

    # Calculate final test metrics (on full data for reporting)
    y_pred = model.predict(X)
    final_metrics = calculate_metrics(y, y_pred)

    # Prepare results
    results = {
        'cv_results': cv_results,
        'final_metrics': final_metrics,
        'baseline_mae': baseline_mae,
        'permutation_test': {
            'observed_r2': observed_r2,
            'p_value': p_value,
            'n_permutations': args.n_permutations
        },
        'config': {
            'features_used': required_features,
            'target': target,
            'n_samples': len(features),
            'n_folds': args.n_folds,
            'random_state': args.random_state
        }
    }

    # Save results
    try:
        save_results(results, args.output)
    except IOError as e:
        logger.error(f"Failed to save results: {e}")
        sys.exit(1)

    logger.info("Evaluation complete.")

if __name__ == '__main__':
    main()