import argparse
import json
import logging
import sys
import pickle
import os
import numpy as np
from sklearn.metrics import r2_score
from sklearn.ensemble import RandomForestRegressor

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def load_features(features_path):
    logger = logging.getLogger(__name__)
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    with open(features_path, 'r') as f:
        data = json.load(f)
    if not data:
        raise ValueError("Features file is empty.")
    logger.info(f"Loaded {len(data)} samples from {features_path}")
    return data

def load_model(model_path):
    logger = logging.getLogger(__name__)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Model loaded from {model_path}")
    return model

def calculate_metrics(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    mae = np.mean(np.abs(y_true - y_pred))
    return r2, mae

def calculate_baseline_mae(y_true):
    mean_pred = np.mean(y_true)
    baseline_mae = np.mean(np.abs(y_true - mean_pred))
    return baseline_mae

def calculate_permutation_pvalue(model, X, y, n_permutations=1000, random_state=42):
    """
    T030a: Implement permutation test logic.
    Permute the feature matrix (X) against the target (y) n_permutations times.
    Calculate R² for each permutation. Compute p-value as the fraction of 
    permuted R² values >= observed R².
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting permutation test with {n_permutations} permutations...")

    # Calculate observed R²
    y_pred = model.predict(X)
    observed_r2 = r2_score(y, y_pred)
    logger.info(f"Observed R²: {observed_r2:.4f}")

    # Setup RNG
    rng = np.random.default_rng(random_state)
    n_samples = X.shape[0]
    permuted_r2s = np.zeros(n_permutations)

    for i in range(n_permutations):
        # Permute X (feature matrix)
        X_permuted = X[rng.permutation(n_samples), :]
        
        # Train a new model on permuted data (to simulate null hypothesis)
        # We use a fresh model to ensure the permutation test is valid
        perm_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=None,
            random_state=random_state + i,
            n_jobs=1  # Single thread for speed in loop
        )
        perm_model.fit(X_permuted, y)
        
        # Calculate R² on permuted data
        y_pred_perm = perm_model.predict(X)
        permuted_r2s[i] = r2_score(y, y_pred_perm)

        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations} completed")

    # Calculate p-value: fraction of permuted R² >= observed R²
    p_value = np.mean(permuted_r2s >= observed_r2)
    
    logger.info(f"Permutation test complete. P-value: {p_value:.4f}")
    logger.info(f"Max permuted R²: {np.max(permuted_r2s):.4f}, Mean permuted R²: {np.mean(permuted_r2s):.4f}")

    return p_value, observed_r2, permuted_r2s

def evaluate_model(model, X_test, y_test):
    logger = logging.getLogger(__name__)
    y_pred = model.predict(X_test)
    r2, mae = calculate_metrics(y_test, y_pred)
    logger.info(f"Evaluation - R²: {r2:.4f}, MAE: {mae:.4f}")
    return r2, mae, y_pred

def save_results(results, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Results saved to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate trained model')
    parser.add_argument('--features', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json',
                        help='Path to features JSON')
    parser.add_argument('--model', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/model.pkl',
                        help='Path to model pickle')
    parser.add_argument('--results', type=str, default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json',
                        help='Path to save results')
    parser.add_argument('--n-permutations', type=int, default=1000,
                        help='Number of permutations for test')
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()

    logger.info("Loading features...")
    data = load_features(args.features)

    # Reconstruct X and y for evaluation
    feature_keys = ['variance', 'entropy', 'skewness', 'kurtosis', 'global_eigenvalue', 'entanglement_score']
    target_key = 'fidelity_loss'
    
    X = np.array([[record.get(k, 0.0) for k in feature_keys] for record in data])
    y = np.array([record.get(target_key, 0.0) for record in data])

    # Split data same as training
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    logger.info("Loading model...")
    model = load_model(args.model)

    logger.info("Evaluating model...")
    r2, mae, y_pred = evaluate_model(model, X_test, y_test)

    logger.info("Running permutation test (T030a)...")
    p_value, observed_r2, perm_r2s = calculate_permutation_pvalue(
        model, X_test, y_test, n_permutations=args.n_permutations, random_state=42
    )

    baseline_mae = calculate_baseline_mae(y_test)

    results = {
        'r2': float(r2),
        'mae': float(mae),
        'baseline_mae': float(baseline_mae),
        'permutation_p_value': float(p_value),
        'observed_r2': float(observed_r2),
        'n_permutations': args.n_permutations,
        'test_size': len(X_test)
    }

    logger.info("Saving results...")
    save_results(results, args.results)

    return results

if __name__ == '__main__':
    main()