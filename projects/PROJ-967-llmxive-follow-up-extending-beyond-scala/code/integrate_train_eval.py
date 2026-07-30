"""
Integration Module for Training and Evaluation.

This module implements T031: Integrate training and evaluation.
It orchestrates the full pipeline from data loading to final results.
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
from sklearn.dummy import DummyRegressor
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)

def setup_logging(log_level=logging.INFO):
    """Configure logging for the module."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def ensure_directories(paths):
    """Ensure all required directories exist."""
    for path in paths:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).mkdir(parents=True, exist_ok=True)

def load_features(features_path):
    """Load features from JSON."""
    with open(features_path, 'r') as f:
        return json.load(f)

def prepare_data(features, test_size=0.2, random_state=42, n_bins=5):
    """Prepare data with quantile-based stratification."""
    feature_keys = [
        'variance', 'entropy', 'score_magnitude', 'mahalanobis_distance',
        'dominant_eigenvalue', 'fidelity_loss'
    ]

    valid_features = []
    for i, f in enumerate(features):
        if all(key in f and f[key] is not None for key in feature_keys):
            valid_features.append((i, f))

    logger.info(f"Valid samples: {len(valid_features)}/{len(features)}")

    X = np.array([[f[k] for k in feature_keys[:-1]] for _, f in valid_features])
    y = np.array([f['fidelity_loss'] for _, f in valid_features])
    indices = np.array([i for i, _ in valid_features])

    y_bins = np.digitize(y, np.percentile(y, np.linspace(0, 100, n_bins + 1)[1:-1]))
    y_bins = np.clip(y_bins, 0, n_bins - 1)

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

def train_model(X_train, y_train, n_estimators=100, random_state=42):
    """Train Random Forest model."""
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=None,
        random_state=random_state,
        n_jobs=2
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    """Evaluate model on test set."""
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    return {'r2': r2, 'mae': mae, 'predictions': y_pred.tolist()}

def run_cross_validation(X, y, cv_folds=5, random_state=42):
    """Run k-fold cross-validation."""
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=random_state,
        n_jobs=2
    )

    n_bins = 5
    y_bins = np.digitize(y, np.percentile(y, np.linspace(0, 100, n_bins + 1)[1:-1]))
    y_bins = np.clip(y_bins, 0, n_bins - 1)

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    scores = cross_val_score(model, X, y, cv=cv, scoring='r2')

    return scores

def calculate_permutation_pvalue(X_train, y_train, n_permutations=1000, random_state=42):
    """Calculate permutation test p-value."""
    np.random.seed(random_state)

    model = RandomForestRegressor(n_estimators=100, random_state=random_state, n_jobs=2)
    model.fit(X_train, y_train)
    y_pred_orig = model.predict(X_train)
    r2_orig = r2_score(y_train, y_pred_orig)

    r2_permuted = []
    for i in range(n_permutations):
        X_shuffled = X_train.copy()
        np.random.shuffle(X_shuffled)

        perm_model = RandomForestRegressor(n_estimators=100, random_state=random_state + i, n_jobs=2)
        perm_model.fit(X_shuffled, y_train)
        y_pred_perm = perm_model.predict(X_shuffled)
        r2_perm = r2_score(y_train, y_pred_perm)
        r2_permuted.append(r2_perm)

    r2_permuted = np.array(r2_permuted)
    p_value = np.sum(r2_permuted >= r2_orig) / n_permutations

    return {
        'p_value': p_value,
        'observed_r2': r2_orig,
        'permuted_r2_mean': float(r2_permuted.mean()),
        'permuted_r2_std': float(r2_permuted.std())
    }

def calculate_mean_baseline(X_train, y_train, X_test, y_test):
    """Train and evaluate mean baseline."""
    mean_model = DummyRegressor(strategy='mean')
    mean_model.fit(X_train, y_train)
    y_pred_mean = mean_model.predict(X_test)

    r2 = r2_score(y_test, y_pred_mean)
    mae = mean_absolute_error(y_test, y_pred_mean)

    return {
        'r2': r2,
        'mae': mae,
        'predictions': y_pred_mean.tolist()
    }

def run_integration_pipeline(
    features_path,
    split_output,
    model_output,
    results_output,
    comparison_output,
    test_size=0.2,
    n_estimators=100,
    n_permutations=1000,
    random_state=42
):
    """Run the full integration pipeline."""
    logger.info("Loading features...")
    features = load_features(features_path)

    logger.info("Preparing data...")
    X_train, X_test, y_train, y_test, split_config = prepare_data(
        features, test_size, random_state
    )

    # Save split config
    with open(split_output, 'w') as f:
        json.dump(split_config, f, indent=2)

    logger.info("Training model...")
    model = train_model(X_train, y_train, n_estimators, random_state)

    logger.info("Evaluating model...")
    test_metrics = evaluate_model(model, X_test, y_test)
    train_metrics = evaluate_model(model, X_train, y_train)

    logger.info("Running cross-validation...")
    cv_scores = run_cross_validation(
        np.vstack([X_train, X_test]),
        np.concatenate([y_train, y_test])
    )

    logger.info("Running permutation test...")
    permutation_results = calculate_permutation_pvalue(X_train, y_train, n_permutations, random_state)

    logger.info("Calculating mean baseline...")
    mean_baseline = calculate_mean_baseline(X_train, y_train, X_test, y_test)

    # Paired t-test on residuals
    residuals_rf = y_test - np.array(test_metrics['predictions'])
    residuals_mean = y_test - np.array(mean_baseline['predictions'])
    t_stat, p_value = stats.ttest_rel(residuals_mean, residuals_rf)

    is_significantly_better = (t_stat < 0) and (p_value < 0.05)
    r2_positive = test_metrics['r2'] > 0.0
    task_passed = is_significantly_better or r2_positive

    # Save model
    with open(model_output, 'wb') as f:
        pickle.dump(model, f)

    # Save results
    results = {
        'model_metrics': {
            'train': train_metrics,
            'test': test_metrics
        },
        'cross_validation': {
            'scores': cv_scores.tolist(),
            'mean': float(cv_scores.mean()),
            'std': float(cv_scores.std())
        },
        'permutation_test': permutation_results,
        'mean_baseline': mean_baseline,
        'statistical_test': {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'is_significantly_better': is_significantly_better
        },
        'task_passed': task_passed,
        'pass_reason': 'Significant improvement (t-test)' if is_significantly_better else 'R2 > 0.0' if r2_positive else 'Failed'
    }

    with open(results_output, 'w') as f:
        json.dump(results, f, indent=2)

    # Save comparison
    comparison = {
        'random_forest': {'r2': test_metrics['r2'], 'mae': test_metrics['mae']},
        'mean_baseline': {'r2': mean_baseline['r2'], 'mae': mean_baseline['mae']},
        'statistical_test': {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'is_significantly_better': is_significantly_better
        },
        'task_passed': task_passed
    }

    with open(comparison_output, 'w') as f:
        json.dump(comparison, f, indent=2)

    return results

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run integrated training and evaluation pipeline.')
    parser.add_argument('--features', type=str, required=True, help='Path to features JSON')
    parser.add_argument('--split-output', type=str, required=True, help='Path to save split config')
    parser.add_argument('--model-output', type=str, required=True, help='Path to save model')
    parser.add_argument('--results-output', type=str, required=True, help='Path to save results')
    parser.add_argument('--comparison-output', type=str, required=True, help='Path to save comparison')
    parser.add_argument('--test-size', type=float, default=0.2)
    parser.add_argument('--n-estimators', type=int, default=100)
    parser.add_argument('--n-permutations', type=int, default=1000)
    parser.add_argument('--random-state', type=int, default=42)
    parser.add_argument('--log-level', type=str, default='INFO')
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    setup_logging(getattr(logging, args.log_level))

    logger.info("Starting integrated pipeline...")

    try:
        ensure_directories([
            args.split_output, args.model_output,
            args.results_output, args.comparison_output
        ])

        results = run_integration_pipeline(
            args.features,
            args.split_output,
            args.model_output,
            args.results_output,
            args.comparison_output,
            args.test_size,
            args.n_estimators,
            args.n_permutations,
            args.random_state
        )

        logger.info(f"Pipeline completed. Task passed: {results['task_passed']}")
        sys.exit(0 if results['task_passed'] else 1)

    except Exception as e:
        logger.error(f"ERROR: {str(e)}", exc_info=True)
        sys.exit(2)

if __name__ == '__main__':
    main()
