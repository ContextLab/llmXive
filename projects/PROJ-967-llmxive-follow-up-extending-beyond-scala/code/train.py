"""
Training Module for llmXive Follow-up.

This module implements T027a, T027b, T028, and T030a.
It handles data preparation, Random Forest training, cross-validation,
and permutation test for p-value calculation.
"""

import argparse
import json
import logging
import os
import sys
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import r2_score, mean_absolute_error
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

def setup_logging(log_level=logging.INFO):
    """Configure logging for the module."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_features(features_path):
    """
    Load features from JSON.

    Args:
        features_path: Path to the features JSON file.

    Returns:
        List of feature dictionaries.
    """
    with open(features_path, 'r') as f:
        return json.load(f)

def prepare_data(features, test_size=0.2, random_state=42, n_bins=5):
    """
    Prepare data for training with quantile-based stratification.

    Args:
        features: List of feature dictionaries.
        test_size: Proportion of data for testing.
        random_state: Random seed for reproducibility.
        n_bins: Number of bins for quantile-based stratification.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test, split_config).
    """
    # Extract features and target
    feature_keys = [
        'variance', 'entropy', 'score_magnitude', 'mahalanobis_distance',
        'dominant_eigenvalue', 'fidelity_loss'
    ]

    # Filter out rows with missing values
    valid_features = []
    for i, f in enumerate(features):
        if all(key in f and f[key] is not None for key in feature_keys):
            valid_features.append((i, f))

    logger.info(f"Valid samples: {len(valid_features)}/{len(features)}")

    X = np.array([[f[k] for k in feature_keys[:-1]] for _, f in valid_features])
    y = np.array([f['fidelity_loss'] for _, f in valid_features])
    indices = np.array([i for i, _ in valid_features])

    # Quantile-based binning for stratification
    y_bins = np.digitize(y, np.percentile(y, np.linspace(0, 100, n_bins + 1)[1:-1]))
    y_bins = np.clip(y_bins, 0, n_bins - 1)

    # Split data with stratification
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, indices,
        test_size=test_size,
        random_state=random_state,
        stratify=y_bins
    )

    split_config = {
        'train_indices': idx_train.tolist(),
        'test_indices': idx_test.tolist(),
        'test_size': test_size,
        'random_state': random_state,
        'n_bins': n_bins
    }

    return X_train, X_test, y_train, y_test, split_config

def train_and_evaluate(X_train, X_test, y_train, y_test, n_estimators=100, random_state=42):
    """
    Train Random Forest and evaluate on test set.

    Args:
        X_train: Training features.
        X_test: Test features.
        y_train: Training targets.
        y_test: Test targets.
        n_estimators: Number of trees in the forest.
        random_state: Random seed.

    Returns:
        Trained model and metrics dictionary.
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=None,
        random_state=random_state,
        n_jobs=2  # CPU-only
    )

    model.fit(X_train, y_train)

    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Metrics
    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    mae_train = mean_absolute_error(y_train, y_pred_train)
    mae_test = mean_absolute_error(y_test, y_pred_test)

    metrics = {
        'r2_train': r2_train,
        'r2_test': r2_test,
        'mae_train': mae_train,
        'mae_test': mae_test,
        'test_predictions': y_pred_test.tolist(),
        'train_predictions': y_pred_train.tolist()
    }

    logger.info(f"Train R2: {r2_train:.4f}, Test R2: {r2_test:.4f}")
    logger.info(f"Train MAE: {mae_train:.4f}, Test MAE: {mae_test:.4f}")

    return model, metrics

def run_cross_validation(X, y, cv_folds=5, random_state=42):
    """
    Run k-fold cross-validation.

    Args:
        X: Features.
        y: Targets.
        cv_folds: Number of CV folds.
        random_state: Random seed.

    Returns:
        Cross-validation scores.
    """
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=random_state,
        n_jobs=2
    )

    # Use quantile binning for stratified CV
    n_bins = 5
    y_bins = np.digitize(y, np.percentile(y, np.linspace(0, 100, n_bins + 1)[1:-1]))
    y_bins = np.clip(y_bins, 0, n_bins - 1)

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')

    logger.info(f"CV R2 scores: {scores}")
    logger.info(f"CV Mean R2: {scores.mean():.4f} (+/- {scores.std():.4f})")

    return scores

def calculate_permutation_pvalue(X_train, y_train, model_class, n_permutations=1000, random_state=42):
    """
    Calculate permutation test p-value.

    Permute the feature matrix (X) against the target (y) n_permutations times.
    Calculate R2 for each permutation. Compute p-value as the fraction of
    permuted R2 values >= observed R2.

    Args:
        X_train: Training features.
        y_train: Training targets.
        model_class: Model class to use (e.g., RandomForestRegressor).
        n_permutations: Number of permutations.
        random_state: Random seed.

    Returns:
        Permutation test p-value.
    """
    np.random.seed(random_state)

    # Train original model and get observed R2
    original_model = model_class(n_estimators=100, random_state=random_state, n_jobs=2)
    original_model.fit(X_train, y_train)
    y_pred_orig = original_model.predict(X_train)
    r2_orig = r2_score(y_train, y_pred_orig)

    logger.info(f"Observed R2: {r2_orig:.4f}")

    # Permutation test
    r2_permuted = []
    for i in range(n_permutations):
        # Shuffle X (not y)
        X_shuffled = X_train.copy()
        np.random.shuffle(X_shuffled)

        # Train on shuffled data
        perm_model = model_class(n_estimators=100, random_state=random_state + i, n_jobs=2)
        perm_model.fit(X_shuffled, y_train)
        y_pred_perm = perm_model.predict(X_shuffled)
        r2_perm = r2_score(y_train, y_pred_perm)
        r2_permuted.append(r2_perm)

    r2_permuted = np.array(r2_permuted)

    # Calculate p-value: fraction of permuted R2 >= observed R2
    p_value = np.sum(r2_permuted >= r2_orig) / n_permutations

    logger.info(f"Permutation p-value: {p_value:.4f}")
    logger.info(f"Permuted R2 mean: {r2_permuted.mean():.4f}, std: {r2_permuted.std():.4f}")

    return {
        'p_value': p_value,
        'observed_r2': r2_orig,
        'permuted_r2_mean': float(r2_permuted.mean()),
        'permuted_r2_std': float(r2_permuted.std()),
        'n_permutations': n_permutations
    }

def save_results(model, metrics, cv_scores, permutation_results, split_config, output_path):
    """
    Save all training results.

    Args:
        model: Trained model.
        metrics: Model metrics.
        cv_scores: Cross-validation scores.
        permutation_results: Permutation test results.
        split_config: Split configuration.
        output_path: Path to save results.
    """
    results = {
        'metrics': metrics,
        'cross_validation': {
            'scores': cv_scores.tolist(),
            'mean': float(cv_scores.mean()),
            'std': float(cv_scores.std())
        },
        'permutation_test': permutation_results,
        'split_config': split_config
    }

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {output_path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Train Random Forest model with CV and permutation test.'
    )
    parser.add_argument(
        '--features',
        type=str,
        required=True,
        help='Path to features JSON file'
    )
    parser.add_argument(
        '--split-output',
        type=str,
        required=True,
        help='Path to save split configuration'
    )
    parser.add_argument(
        '--model-output',
        type=str,
        required=True,
        help='Path to save trained model (for T027c)'
    )
    parser.add_argument(
        '--results-output',
        type=str,
        required=True,
        help='Path to save training results'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Proportion of data for testing'
    )
    parser.add_argument(
        '--n-estimators',
        type=int,
        default=100,
        help='Number of trees in the forest'
    )
    parser.add_argument(
        '--n-permutations',
        type=int,
        default=1000,
        help='Number of permutations for p-value calculation'
    )
    parser.add_argument(
        '--random-state',
        type=int,
        default=42,
        help='Random seed'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    return parser.parse_args()

def main():
    """Main entry point for training."""
    args = parse_args()
    setup_logging(getattr(logging, args.log_level))

    logger.info("Starting model training...")

    try:
        # Load features
        logger.info(f"Loading features from {args.features}")
        features = load_features(args.features)

        # Prepare data
        logger.info("Preparing data...")
        X_train, X_test, y_train, y_test, split_config = prepare_data(
            features,
            test_size=args.test_size,
            random_state=args.random_state
        )

        # Save split configuration
        split_output_path = Path(args.split_output)
        split_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(split_output_path, 'w') as f:
            json.dump(split_config, f, indent=2)
        logger.info(f"Split configuration saved to {split_output_path}")

        # Train and evaluate
        logger.info("Training Random Forest...")
        model, metrics = train_and_evaluate(
            X_train, X_test, y_train, y_test,
            n_estimators=args.n_estimators,
            random_state=args.random_state
        )

        # Cross-validation
        logger.info("Running cross-validation...")
        cv_scores = run_cross_validation(
            np.vstack([X_train, X_test]),
            np.concatenate([y_train, y_test]),
            cv_folds=5,
            random_state=args.random_state
        )

        # Permutation test
        logger.info("Running permutation test...")
        permutation_results = calculate_permutation_pvalue(
            X_train, y_train,
            RandomForestRegressor,
            n_permutations=args.n_permutations,
            random_state=args.random_state
        )

        # Save model (for T027c)
        model_output_path = Path(args.model_output)
        model_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_output_path, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"Model saved to {model_output_path}")

        # Save results
        logger.info("Saving results...")
        save_results(
            model, metrics, cv_scores, permutation_results,
            split_config, args.results_output
        )

        logger.info("Training completed successfully.")
        sys.exit(0)

    except Exception as e:
        logger.error(f"ERROR: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
