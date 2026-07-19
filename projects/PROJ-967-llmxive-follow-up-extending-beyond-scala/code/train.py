"""
Training Module for Random Forest Regressor.

This module trains a CPU-based Random Forest model to predict fidelity loss
using entanglement features, with k-fold cross-validation.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_squared_error, r2_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_features(filepath: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load features and target from JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Tuple of (features_matrix, target_vector)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    per_sample_stats = data.get("per_sample_stats", {})
    fidelity_loss = data.get("fidelity_loss", [])
    
    # Extract features
    features = []
    targets = []
    
    for sample_id, stats in per_sample_stats.items():
        # Use variance, entropy, skewness, kurtosis as features
        feature_vector = [
            stats.get("variance", 0),
            stats.get("entropy", 0),
            stats.get("skewness", 0),
            stats.get("kurtosis", 0)
        ]
        features.append(feature_vector)
    
    # Align targets with features
    # Note: fidelity_loss might have fewer entries due to missing annotations
    # We need to match them by index after filtering
    valid_indices = []
    for i, sample_id in enumerate(per_sample_stats.keys()):
        if i < len(fidelity_loss):
            valid_indices.append(i)
    
    features = np.array(features)
    targets = np.array(fidelity_loss[:len(features)])
    
    return features, targets

def train_and_evaluate(features: np.ndarray, targets: np.ndarray, n_folds: int = 5) -> Dict[str, Any]:
    """
    Train Random Forest model with k-fold cross-validation.
    
    Args:
        features: Feature matrix
        targets: Target vector
        n_folds: Number of CV folds
        
    Returns:
        Dictionary with training results
    """
    # Initialize model (CPU-only)
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=2  # CPU-only
    )
    
    # Cross-validation
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, features, targets, cv=kf, scoring='r2')
    
    # Train final model on all data
    model.fit(features, targets)
    
    # Predictions on training data (for R2 and MAE calculation)
    predictions = model.predict(features)
    r2 = r2_score(targets, predictions)
    mae = np.mean(np.abs(predictions - targets))
    
    return {
        "cv_r2_mean": float(np.mean(cv_scores)),
        "cv_r2_std": float(np.std(cv_scores)),
        "final_r2": float(r2),
        "mae": float(mae),
        "model_params": model.get_params()
    }

def save_results(results: Dict[str, Any], output_path: str):
    """
    Save training results to JSON file.
    
    Args:
        results: Dictionary of results
        output_path: Output path for the JSON file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Train Random Forest model")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/features.json",
        help="Input JSON file with features"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/training_results.json",
        help="Output JSON file for results"
    )
    parser.add_argument(
        "--n-folds",
        type=int,
        default=5,
        help="Number of CV folds"
    )
    return parser.parse_args()

def main():
    """Main entry point for the training script."""
    args = parse_args()
    
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Load features
    logger.info(f"Loading features from {args.input}")
    features, targets = load_features(args.input)
    
    if len(features) == 0:
        logger.error("No features loaded")
        sys.exit(1)
    
    logger.info(f"Loaded {len(features)} samples")
    
    # Train and evaluate
    logger.info("Training model with cross-validation...")
    results = train_and_evaluate(features, targets, args.n_folds)
    
    # Save results
    logger.info(f"Saving results to {args.output}")
    save_results(results, args.output)
    
    # Print summary
    logger.info(f"Cross-validation R²: {results['cv_r2_mean']:.4f} ± {results['cv_r2_std']:.4f}")
    logger.info(f"Final R²: {results['final_r2']:.4f}")
    logger.info(f"MAE: {results['mae']:.4f}")
    
    return 0

if __name__ == "__main__":
    exit(main())
