"""
Evaluation script for User Story 3: Predictive Modeling and Validation.

Implements evaluation metrics calculation, baseline comparison, and permutation test.
Reads features from data/processed/features.json, trains model, and writes final metrics.
"""
import argparse
import json
import logging
import sys
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.utils import shuffle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Evaluate model performance with permutation test.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/features.json',
        help='Path to input features JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/results.json',
        help='Path to output results JSON file'
    )
    parser.add_argument(
        '--n_estimators',
        type=int,
        default=100,
        help='Number of trees in the Random Forest'
    )
    parser.add_argument(
        '--random_state',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--n_jobs',
        type=int,
        default=2,
        help='Number of CPU cores to use (-1 for all)'
    )
    parser.add_argument(
        '--n_permutations',
        type=int,
        default=100,
        help='Number of permutations for permutation test'
    )
    return parser.parse_args()


def load_features(input_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load features and target from JSON file.
    
    Args:
        input_path: Path to features JSON file
        
    Returns:
        Tuple of (X, y, feature_names)
    """
    logger.info(f"Loading features from {input_path}")
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    samples = data.get('samples', [])
    if not samples:
        raise ValueError("No samples found in input file")
    
    # Define feature columns
    feature_cols = ['variance', 'range', 'entropy', 'skewness', 'kurtosis']
    
    X = []
    y = []
    
    for sample in samples:
        features = [sample.get(col, 0.0) for col in feature_cols]
        target = sample.get('fidelity_loss', 0.0)
        X.append(features)
        y.append(target)
    
    X = np.array(X, dtype=np.float64)
    y = np.array(y, dtype=np.float64)
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_cols)} features")
    return X, y, feature_cols


def load_model(X: np.ndarray, y: np.ndarray, n_estimators: int = 100, 
              random_state: int = 42, n_jobs: int = 2) -> RandomForestRegressor:
    """
    Load (train) a Random Forest model.
    
    Args:
        X: Feature matrix
        y: Target vector
        n_estimators: Number of trees
        random_state: Random seed
        n_jobs: Number of CPU cores
        
    Returns:
        Trained Random Forest model
    """
    logger.info("Training Random Forest model")
    
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=n_jobs
    )
    model.fit(X, y)
    
    return model


def calculate_metrics(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Calculate model performance metrics.
    
    Args:
        model: Trained model
        X: Feature matrix
        y: Target vector
        
    Returns:
        Dictionary with R² and MAE
    """
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    logger.info(f"Model metrics - R²: {r2:.4f}, MAE: {mae:.4f}")
    return {'r2': r2, 'mae': mae}


def calculate_baseline_mae(y: np.ndarray) -> float:
    """
    Calculate baseline MAE (predicting mean of y).
    
    Args:
        y: Target vector
        
    Returns:
        Baseline MAE
    """
    baseline_pred = np.full_like(y, np.mean(y))
    baseline_mae = mean_absolute_error(y, baseline_pred)
    logger.info(f"Baseline MAE (mean prediction): {baseline_mae:.4f}")
    return baseline_mae


def perform_permutation_test(
    model: RandomForestRegressor,
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 100,
    random_state: int = 42
) -> float:
    """
    Perform permutation test to assess statistical significance.
    
    Compares model MAE against null baseline by permuting target variable.
    
    Args:
        model: Trained model
        X: Feature matrix
        y: Target vector
        n_permutations: Number of permutations
        random_state: Random seed
        
    Returns:
        p-value from permutation test
    """
    logger.info(f"Performing permutation test with {n_permutations} permutations")
    
    # Calculate actual model MAE
    actual_mae = mean_absolute_error(y, model.predict(X))
    
    # Calculate null distribution by permuting y
    null_maes = []
    rng = np.random.RandomState(random_state)
    
    for i in range(n_permutations):
        # Permute target variable
        y_permuted = y.copy()
        rng.shuffle(y_permuted)
        
        # Train model on permuted data
        perm_model = RandomForestRegressor(
            n_estimators=model.n_estimators,
            random_state=random_state,
            n_jobs=model.n_jobs
        )
        perm_model.fit(X, y_permuted)
        
        # Calculate MAE on permuted data
        perm_mae = mean_absolute_error(y_permuted, perm_model.predict(X))
        null_maes.append(perm_mae)
    
    null_maes = np.array(null_maes)
    
    # Calculate p-value: proportion of null MAEs <= actual MAE
    # (lower MAE is better, so we check if actual is significantly better)
    p_value = np.sum(null_maes <= actual_mae) / n_permutations
    
    logger.info(f"Permutation test results:")
    logger.info(f"  Actual MAE: {actual_mae:.4f}")
    logger.info(f"  Null MAE mean: {np.mean(null_maes):.4f}")
    logger.info(f"  Null MAE std: {np.std(null_maes):.4f}")
    logger.info(f"  p-value: {p_value:.4f}")
    
    return p_value


def evaluate_model(
    X: np.ndarray,
    y: np.ndarray,
    n_estimators: int = 100,
    random_state: int = 42,
    n_jobs: int = 2,
    n_permutations: int = 100
) -> Dict[str, Any]:
    """
    Full evaluation pipeline: train model, calculate metrics, perform permutation test.
    
    Args:
        X: Feature matrix
        y: Target vector
        n_estimators: Number of trees
        random_state: Random seed
        n_jobs: Number of CPU cores
        n_permutations: Number of permutations for test
        
    Returns:
        Dictionary with all evaluation metrics
    """
    # Train model
    model = load_model(X, y, n_estimators, random_state, n_jobs)
    
    # Calculate metrics
    metrics = calculate_metrics(model, X, y)
    
    # Calculate baseline
    baseline_mae = calculate_baseline_mae(y)
    
    # Perform permutation test
    p_value = perform_permutation_test(model, X, y, n_permutations, random_state)
    
    # Prepare results
    results = {
        'r2': metrics['r2'],
        'mae': metrics['mae'],
        'baseline_mae': baseline_mae,
        'permutation_p_value': p_value,
        'model_params': {
            'n_estimators': n_estimators,
            'random_state': random_state,
            'n_jobs': n_jobs
        },
        'test_params': {
            'n_permutations': n_permutations
        },
        'n_samples': len(X),
        'n_features': X.shape[1]
    }
    
    logger.info(f"Evaluation complete. R²: {metrics['r2']:.4f}, MAE: {metrics['mae']:.4f}, p-value: {p_value:.4f}")
    return results


def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save results to JSON file.
    
    Args:
        results: Dictionary of metrics
        output_path: Path to output file
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")


def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    try:
        # Load features
        X, y, feature_names = load_features(args.input)
        
        # Evaluate model
        results = evaluate_model(
            X, y,
            n_estimators=args.n_estimators,
            random_state=args.random_state,
            n_jobs=args.n_jobs,
            n_permutations=args.n_permutations
        )
        
        # Save results
        save_results(results, args.output)
        
        logger.info("Evaluation completed successfully")
        
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
