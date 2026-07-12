"""
Training script for User Story 3: Predictive Modeling and Validation.

Implements Random Forest regressor to predict fidelity loss using entanglement features.
Reads features from data/processed/features.json, trains model, and writes metrics.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import mean_absolute_error, r2_score
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
        description='Train Random Forest model to predict fidelity loss.'
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


def train_and_evaluate(
    X: np.ndarray, 
    y: np.ndarray,
    n_estimators: int = 100,
    random_state: int = 42,
    n_jobs: int = 2
) -> Dict[str, Any]:
    """
    Train Random Forest model with 5-fold cross-validation.
    
    Args:
        X: Feature matrix
        y: Target vector (fidelity loss)
        n_estimators: Number of trees
        random_state: Random seed
        n_jobs: Number of CPU cores
        
    Returns:
        Dictionary with training metrics
    """
    logger.info("Starting model training with 5-fold cross-validation")
    
    # Create Random Forest regressor
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=n_jobs,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1
    )
    
    # Prepare stratified splits for cross-validation
    # Since we're predicting a continuous variable, we create bins for stratification
    y_bins = np.digitize(y, bins=np.percentile(y, [20, 40, 60, 80]))
    
    # 5-fold cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    
    # Calculate cross-validation scores
    cv_r2_scores = cross_val_score(model, X, y_bins, cv=cv, scoring='r2')
    
    logger.info(f"Cross-validation R² scores: {cv_r2_scores}")
    logger.info(f"Mean R²: {cv_r2_scores.mean():.4f} (+/- {cv_r2_scores.std() * 2:.4f})")
    
    # Train final model on all data
    model.fit(X, y)
    
    # Predict on training data to calculate MAE and R²
    y_pred = model.predict(X)
    mae = mean_absolute_error(y, y_pred)
    r2 = r2_score(y, y_pred)
    
    # Feature importance
    feature_importances = dict(zip(
        ['variance', 'range', 'entropy', 'skewness', 'kurtosis'],
        model.feature_importances_
    ))
    
    results = {
        'cv_r2_mean': float(cv_r2_scores.mean()),
        'cv_r2_std': float(cv_r2_scores.std()),
        'cv_r2_scores': [float(s) for s in cv_r2_scores],
        'train_r2': float(r2),
        'train_mae': float(mae),
        'feature_importances': feature_importances,
        'n_samples': len(X),
        'n_features': X.shape[1],
        'model_params': {
            'n_estimators': n_estimators,
            'random_state': random_state,
            'n_jobs': n_jobs
        }
    }
    
    logger.info(f"Training complete. MAE: {mae:.4f}, R²: {r2:.4f}")
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
        
        # Train and evaluate
        results = train_and_evaluate(
            X, y,
            n_estimators=args.n_estimators,
            random_state=args.random_state,
            n_jobs=args.n_jobs
        )
        
        # Save results
        save_results(results, args.output)
        
        logger.info("Task completed successfully")
        
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
