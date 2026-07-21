import argparse
import json
import logging
import os
import sys
import pickle
import tracemalloc
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.inspection import permutation_importance

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)

def load_features(logger, feature_path):
    """Load features from JSON file."""
    logger.info(f"Loading features from {feature_path}")
    if not os.path.exists(feature_path):
        raise FileNotFoundError(f"Feature file not found: {feature_path}")
    
    with open(feature_path, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError("Expected features to be a list of records")
    
    if len(data) == 0:
        raise ValueError("Feature file is empty")
    
    logger.info(f"Loaded {len(data)} feature records")
    return data

def prepare_data(data, logger):
    """
    Prepare X (features) and y (target) from loaded data.
    
    Expected keys in each record (based on T025/T024):
    - 'dominant_eigenvalue': Global entanglement score
    - 'variance': Per-sample variance
    - 'entropy': Per-sample entropy
    - 'fidelity_loss': Target variable (MAE between student scalar and human annotation)
    
    We also include 'skewness' and 'kurtosis' if present (from T022b).
    """
    # Define feature columns
    feature_cols = [
        'dominant_eigenvalue',
        'variance',
        'entropy',
        'skewness',
        'kurtosis',
        'dimensional_fidelity_loss'  # Sometimes named differently, check data
    ]
    
    # Filter to only existing columns
    if data:
        existing_cols = [c for c in feature_cols if c in data[0]]
        if 'fidelity_loss' in data[0] and 'fidelity_loss' not in existing_cols:
            existing_cols.append('fidelity_loss')
        feature_cols = existing_cols
    
    if not feature_cols:
        raise ValueError("No feature columns found in data")
    
    logger.info(f"Using feature columns: {feature_cols}")
    
    X = []
    y = []
    sample_ids = []
    
    for record in data:
        # Extract features
        row = []
        for col in feature_cols:
            val = record.get(col)
            if val is None:
                val = 0.0  # Handle missing values gracefully
            row.append(float(val))
        X.append(row)
        
        # Extract target (fidelity loss)
        target = record.get('fidelity_loss')
        if target is None:
            target = record.get('dimensional_fidelity_loss')
        if target is None:
            raise ValueError("Target variable 'fidelity_loss' or 'dimensional_fidelity_loss' not found in record")
        y.append(float(target))
        
        sample_ids.append(record.get('sample_id', len(y)))
    
    X = np.array(X)
    y = np.array(y)
    
    logger.info(f"Prepared data: X shape={X.shape}, y shape={y.shape}")
    return X, y, sample_ids

def train_and_evaluate(X, y, logger):
    """
    Train RandomForestRegressor with specified parameters.
    Returns trained model and evaluation metrics.
    """
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    logger.info(f"Train/Test split: {len(X_train)}/{len(X_test)} samples")
    
    # Configure Random Forest
    # n_jobs=2 for CPU-only execution as per T027a
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2
    )
    
    # Train
    logger.info("Training Random Forest model...")
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    logger.info(f"Test Metrics: R²={r2:.4f}, MAE={mae:.4f}, RMSE={rmse:.4f}")
    
    # Cross-validation (5-fold)
    logger.info("Running 5-fold cross-validation...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2', n_jobs=2)
    logger.info(f"CV R² scores: {cv_scores}")
    logger.info(f"CV Mean R²: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    # Permutation test for feature importance significance
    logger.info("Running permutation test...")
    perm_result = permutation_importance(
        model, X_test, y_test, 
        n_repeats=100, 
        random_state=42, 
        n_jobs=2
    )
    
    # Calculate p-value: fraction of permuted R² >= observed R²
    # We simulate this by checking if permuted importance is significantly different
    # For a proper permutation test on R², we'd need to retrain on permuted data
    # Here we use permutation_importance as a proxy for feature significance
    permutation_p_values = []
    for i, col_name in enumerate(feature_cols):
        # Count how many permuted R² values are >= observed R²
        # permutation_importance returns mean decrease in score
        # A more rigorous test would require retraining, but we'll use the importances
        pass  # Detailed p-value calculation handled in evaluate.py (T030a)
    
    return {
        'model': model,
        'metrics': {
            'r2': r2,
            'mae': mae,
            'rmse': rmse,
            'cv_r2_mean': cv_scores.mean(),
            'cv_r2_std': cv_scores.std()
        },
        'permutation_results': perm_result,
        'feature_names': feature_cols
    }

def save_results(results, output_path, logger):
    """Save model and metrics to disk."""
    # Save model
    model_path = output_path.replace('.json', '.pkl')
    logger.info(f"Saving model to {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump(results['model'], f)
    
    # Save metrics (excluding model object)
    metrics_output = {
        'r2': results['metrics']['r2'],
        'mae': results['metrics']['mae'],
        'rmse': results['metrics']['rmse'],
        'cv_r2_mean': results['metrics']['cv_r2_mean'],
        'cv_r2_std': results['metrics']['cv_r2_std'],
        'feature_names': results['feature_names']
    }
    
    logger.info(f"Saving metrics to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(metrics_output, f, indent=2)
    
    logger.info("Results saved successfully")

def parse_args():
    parser = argparse.ArgumentParser(description="Train Random Forest model on entanglement features")
    parser.add_argument(
        '--features',
        type=str,
        default=str(PROJECT_ROOT / 'data' / 'processed' / 'features.json'),
        help='Path to features JSON file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=str(PROJECT_ROOT / 'results' / 'train_results.json'),
        help='Path to output metrics JSON file'
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
    args = parse_args()
    logger = setup_logging()
    logger.setLevel(getattr(logging, args.log_level))
    
    logger.info("Starting training pipeline")
    tracemalloc.start()
    
    try:
        # Load features
        data = load_features(logger, args.features)
        
        # Prepare data
        X, y, sample_ids = prepare_data(data, logger)
        
        # Train and evaluate
        results = train_and_evaluate(X, y, logger)
        
        # Save results
        save_results(results, args.output, logger)
        
        # Memory usage
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"Peak memory usage: {peak / 10**6:.2f} MB")
        tracemalloc.stop()
        
        logger.info("Training pipeline completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())