import argparse
import json
import logging
import sys
import pickle
import os
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Project root relative to code/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def load_features(features_path):
    logger = logging.getLogger(__name__)
    logger.info(f"Loading features from {features_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    with open(features_path, 'r') as f:
        data = json.load(f)
    
    if not data:
        raise ValueError("Features file is empty")
    
    # Extract features (X) and target (y)
    # Assuming the schema from contracts/output.schema.yaml
    required_keys = ['sample_id', 'variance', 'entropy', 'skewness', 'kurtosis', 
                    'dominant_eigenvalue', 'fidelity_loss']
    
    X = []
    y = []
    sample_ids = []
    
    for record in data:
        # Verify all required keys exist
        for key in required_keys:
            if key not in record:
                raise KeyError(f"Missing required key '{key}' in feature record")
        
        # Features: variance, entropy, skewness, kurtosis, dominant_eigenvalue
        features = [
            record['variance'],
            record['entropy'],
            record['skewness'],
            record['kurtosis'],
            record['dominant_eigenvalue']
        ]
        X.append(features)
        y.append(record['fidelity_loss'])
        sample_ids.append(record['sample_id'])
    
    logger.info(f"Loaded {len(X)} samples")
    return np.array(X), np.array(y), sample_ids

def load_model(model_path):
    logger = logging.getLogger(__name__)
    logger.info(f"Loading model from {model_path}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    return model

def calculate_metrics(y_true, y_pred):
    """Calculate R² and MAE metrics."""
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    return r2, mae

def calculate_baseline_mae(y_true):
    """Calculate baseline MAE using mean predictor."""
    mean_pred = np.mean(y_true)
    return mean_absolute_error(y_true, np.full_like(y_true, mean_pred))

def perform_permutation_test(X, y, model, n_permutations=1000, random_state=42):
    """
    Perform permutation test to validate correlation strength.
    
    Permute the feature matrix (X) against the target (y) n_permutations times.
    Calculate R² for each permutation. Compute p-value as the fraction of 
    permuted R² values >= observed R².
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        model: Trained model to use for R² calculation
        n_permutations: Number of permutations (default: 1000)
        random_state: Random seed for reproducibility (default: 42)
    
    Returns:
        p_value: Fraction of permuted R² >= observed R²
        observed_r2: R² score on original data
        permuted_r2_scores: List of R² scores from permutations
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting permutation test with {n_permutations} permutations")
    
    # Calculate observed R²
    y_pred_observed = model.predict(X)
    observed_r2 = r2_score(y, y_pred_observed)
    logger.info(f"Observed R²: {observed_r2:.6f}")
    
    # Set random state
    rng = np.random.RandomState(random_state)
    
    # Perform permutations
    permuted_r2_scores = []
    
    for i in range(n_permutations):
        # Permute the feature matrix X
        X_permuted = X.copy()
        for j in range(X.shape[1]):
            permutation = rng.permutation(X.shape[0])
            X_permuted[:, j] = X[:, j][permutation]
        
        # Calculate R² on permuted data
        y_pred_permuted = model.predict(X_permuted)
        r2_permuted = r2_score(y, y_pred_permuted)
        permuted_r2_scores.append(r2_permuted)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_permutations} permutations")
    
    # Calculate p-value: fraction of permuted R² >= observed R²
    permuted_r2_scores = np.array(permuted_r2_scores)
    p_value = np.mean(permuted_r2_scores >= observed_r2)
    
    logger.info(f"Permutation test complete. P-value: {p_value:.6f}")
    logger.info(f"Permuted R² stats: mean={np.mean(permuted_r2_scores):.6f}, "
               f"std={np.std(permuted_r2_scores):.6f}, "
               f"max={np.max(permuted_r2_scores):.6f}")
    
    return p_value, observed_r2, permuted_r2_scores

def evaluate_model(model, X, y):
    """Evaluate model on test set and perform permutation test."""
    logger = logging.getLogger(__name__)
    
    # Calculate metrics on original data
    y_pred = model.predict(X)
    r2, mae = calculate_metrics(y, y_pred)
    logger.info(f"Model Metrics - R²: {r2:.6f}, MAE: {mae:.6f}")
    
    # Perform permutation test
    p_value, observed_r2, permuted_scores = perform_permutation_test(
        X, y, model, n_permutations=1000, random_state=42
    )
    
    return {
        'r2': r2,
        'mae': mae,
        'p_value': p_value,
        'observed_r2': observed_r2,
        'permuted_r2_mean': float(np.mean(permuted_scores)),
        'permuted_r2_std': float(np.std(permuted_scores)),
        'permuted_r2_max': float(np.max(permuted_scores)),
        'n_permutations': 1000
    }

def save_results(results, output_path):
    """Save evaluation results to JSON file."""
    logger = logging.getLogger(__name__)
    logger.info(f"Saving results to {output_path}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Results saved successfully")

def parse_args():
    parser = argparse.ArgumentParser(description='Evaluate trained model and perform permutation test')
    parser.add_argument('--features', type=str, 
                      default=os.path.join(PROJECT_ROOT, 'data', 'processed', 'features.json'),
                      help='Path to features JSON file')
    parser.add_argument('--model', type=str,
                      default=os.path.join(PROJECT_ROOT, 'results', 'model.pkl'),
                      help='Path to trained model pickle file')
    parser.add_argument('--output', type=str,
                      default=os.path.join(PROJECT_ROOT, 'results', 'results.json'),
                      help='Path to output results JSON file')
    parser.add_argument('--n-permutations', type=int, default=1000,
                      help='Number of permutations for test (default: 1000)')
    parser.add_argument('--random-state', type=int, default=42,
                      help='Random seed for permutation test (default: 42)')
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    
    try:
        # Load features
        X, y, sample_ids = load_features(args.features)
        
        # Load model
        model = load_model(args.model)
        
        # Evaluate model and perform permutation test
        results = evaluate_model(model, X, y)
        
        # Update results with configuration
        results['n_permutations'] = args.n_permutations
        results['random_state'] = args.random_state
        results['features_path'] = args.features
        results['model_path'] = args.model
        
        # Save results
        save_results(results, args.output)
        
        logger.info("Evaluation complete. Results:")
        logger.info(f"  R²: {results['r2']:.6f}")
        logger.info(f"  MAE: {results['mae']:.6f}")
        logger.info(f"  P-value: {results['p_value']:.6f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())