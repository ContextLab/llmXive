import argparse
import json
import logging
import os
import sys
import pickle
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import r2_score, mean_absolute_error
from scipy.stats import pearsonr
import time

# Import local utilities if needed, but standard library + sklearn are primary
# Assuming features are loaded from data/processed/features.json as per T025

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_features(filepath):
    """Load features from JSON file."""
    logger = logging.getLogger(__name__)
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} samples from {filepath}")
        return data
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        raise

def prepare_data(data, target_key='fidelity_loss', feature_keys=None):
    """Prepare X and y arrays from data."""
    logger = logging.getLogger(__name__)
    if not data:
        raise ValueError("Data is empty")

    if feature_keys is None:
        # Default features based on T025/T022a/T022b
        feature_keys = ['variance', 'entropy', 'skewness', 'kurtosis', 'entanglement_score', 'global_eigenvalue']

    X = []
    y = []
    valid_indices = []

    for i, sample in enumerate(data):
        # Check for missing target
        if target_key not in sample or sample[target_key] is None:
            continue

        # Check for missing features
        if any(key not in sample or sample[key] is None for key in feature_keys):
            continue

        x_row = [sample[k] for k in feature_keys]
        X.append(x_row)
        y.append(sample[target_key])
        valid_indices.append(i)

    if not X or not y:
        raise ValueError("No valid samples found after filtering")

    logger.info(f"Prepared {len(X)} samples with {len(feature_keys)} features")
    return np.array(X), np.array(y), valid_indices

def train_and_evaluate(X, y, test_size=0.2, random_state=42, n_estimators=100):
    """Train Random Forest and evaluate on test set."""
    logger = logging.getLogger(__name__)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=None,
        random_state=random_state,
        n_jobs=2  # CPU-only
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    logger.info(f"Test R²: {r2:.4f}, Test MAE: {mae:.4f}")

    return model, r2, mae, X_test, y_test, y_pred

def run_cross_validation(X, y, cv_folds=5, random_state=42, n_estimators=100):
    """Run k-fold cross-validation."""
    logger = logging.getLogger(__name__)
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=None,
        random_state=random_state,
        n_jobs=2
    )

    cv_scores = cross_val_score(model, X, y, cv=cv_folds, scoring='r2')
    logger.info(f"CV R² scores: {cv_scores}")
    logger.info(f"Mean CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    return cv_scores

def calculate_permutation_pvalue(X, y, model, n_permutations=1000, random_state=42):
    """
    Perform permutation test to validate correlation strength.
    Permute feature matrix X against target y, calculate R² for each,
    and compute p-value as fraction of permuted R² >= observed R².
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting permutation test with {n_permutations} permutations...")

    # First, get observed R² using the provided model on the full data (or a held-out set)
    # For consistency with the task, we'll compute R² on the full dataset using the trained model
    # Note: In a strict test, we'd use a held-out test set, but the task implies using the model's performance
    # against permuted data. We'll compute R² on the full data for the observed value.
    y_pred_observed = model.predict(X)
    r2_observed = r2_score(y, y_pred_observed)
    logger.info(f"Observed R²: {r2_observed:.4f}")

    np.random.seed(random_state)
    permuted_r2_scores = []

    start_time = time.time()

    for i in range(n_permutations):
        # Permute X (feature matrix)
        X_permuted = X.copy()
        # Shuffle each feature column independently or shuffle rows?
        # Task says "Permute the feature matrix (X) against the target (y)"
        # This typically means shuffling the rows of X relative to y, breaking the relationship.
        # We'll shuffle the rows of X.
        perm_indices = np.random.permutation(len(X))
        X_permuted = X_permuted[perm_indices]

        # Train a new model on permuted data (or just compute R² if we assume same model structure?)
        # The task says "Calculate R² for each permutation".
        # To be rigorous, we should retrain the model on the permuted data.
        perm_model = RandomForestRegressor(
            n_estimators=model.n_estimators,
            max_depth=model.max_depth,
            random_state=random_state,
            n_jobs=2
        )
        perm_model.fit(X_permuted, y)
        y_pred_perm = perm_model.predict(X_permuted)
        r2_perm = r2_score(y, y_pred_perm)
        permuted_r2_scores.append(r2_perm)

        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")

    elapsed = time.time() - start_time
    logger.info(f"Permutation test completed in {elapsed:.2f} seconds")

    permuted_r2_scores = np.array(permuted_r2_scores)
    p_value = np.sum(permuted_r2_scores >= r2_observed) / n_permutations

    logger.info(f"Permutation p-value: {p_value:.4f}")
    logger.info(f"Max permuted R²: {permuted_r2_scores.max():.4f}, Min: {permuted_r2_scores.min():.4f}, Mean: {permuted_r2_scores.mean():.4f}")

    return p_value, r2_observed, permuted_r2_scores

def save_results(filepath, r2, mae, p_value, cv_scores=None, permuted_r2_scores=None):
    """Save results to JSON."""
    logger = logging.getLogger(__name__)
    results = {
        'r2': r2,
        'mae': mae,
        'p_value': p_value,
        'cv_mean_r2': cv_scores.mean() if cv_scores is not None else None,
        'cv_std_r2': cv_scores.std() if cv_scores is not None else None,
        'n_permutations': len(permuted_r2_scores) if permuted_r2_scores is not None else 0,
        'permuted_r2_max': permuted_r2_scores.max() if permuted_r2_scores is not None else None,
        'permuted_r2_min': permuted_r2_scores.min() if permuted_r2_scores is not None else None,
        'permuted_r2_mean': permuted_r2_scores.mean() if permuted_r2_scores is not None else None,
    }

    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {filepath}")

def parse_args():
    parser = argparse.ArgumentParser(description='Train and evaluate Random Forest model.')
    parser.add_argument('--input', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json',
                        help='Path to input features JSON')
    parser.add_argument('--output', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/train_results.json',
                        help='Path to output results JSON')
    parser.add_argument('--model-output', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/model.pkl',
                        help='Path to save trained model')
    parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    parser.add_argument('--n-permutations', type=int, default=1000, help='Number of permutations for permutation test')
    parser.add_argument('--random-state', type=int, default=42, help='Random state for reproducibility')
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()

    logger.info("Loading features...")
    data = load_features(args.input)

    logger.info("Preparing data...")
    X, y, valid_indices = prepare_data(data)

    logger.info("Training model...")
    model, r2, mae, X_test, y_test, y_pred = train_and_evaluate(
        X, y, test_size=args.test_size, random_state=args.random_state
    )

    logger.info("Running cross-validation...")
    cv_scores = run_cross_validation(X, y, random_state=args.random_state)

    logger.info("Running permutation test...")
    p_value, r2_observed, permuted_r2_scores = calculate_permutation_pvalue(
        X, y, model, n_permutations=args.n_permutations, random_state=args.random_state
    )

    logger.info("Saving model...")
    with open(args.model_output, 'wb') as f:
        pickle.dump(model, f)

    logger.info("Saving results...")
    save_results(args.output, r2, mae, p_value, cv_scores, permuted_r2_scores)

    logger.info("Training and evaluation completed successfully.")

if __name__ == '__main__':
    main()