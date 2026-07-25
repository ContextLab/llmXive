import argparse
import json
import logging
import os
import sys
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(PROJECT_ROOT / 'logs' / 'train.log')
        ]
    )
    return logging.getLogger(__name__)

def load_features(features_path):
    """Load features from JSON file."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading features from {features_path}")
    with open(features_path, 'r') as f:
        data = json.load(f)
    if not data:
        raise ValueError("Feature file is empty or invalid")
    return data

def prepare_data(data):
    """Prepare X and y from feature data."""
    logger = logging.getLogger(__name__)
    # Extract features and target
    # Expected keys based on output.schema.yaml and T025:
    # sample_id, variance, entropy, skewness, kurtosis, dominant_eigenvalue, fidelity_loss
    X = []
    y = []
    sample_ids = []

    for row in data:
        # Check for required feature keys
        required_features = ['variance', 'entropy', 'skewness', 'kurtosis', 'dominant_eigenvalue']
        if not all(key in row for key in required_features):
            logger.warning(f"Skipping row {row.get('sample_id', 'unknown')}: missing required features")
            continue

        # Check for target
        if 'fidelity_loss' not in row:
            logger.warning(f"Skipping row {row.get('sample_id', 'unknown')}: missing target (fidelity_loss)")
            continue

        features = [row[k] for k in required_features]
        X.append(features)
        y.append(row['fidelity_loss'])
        sample_ids.append(row.get('sample_id', 'unknown'))

    if len(X) == 0:
        raise ValueError("No valid samples found after filtering")

    logger.info(f"Prepared {len(X)} samples with {len(required_features)} features")
    return np.array(X), np.array(y), sample_ids

def train_and_evaluate(X, y, logger):
    """Train Random Forest and evaluate on test set."""
    logger.info("Splitting data (80/20)")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")

    logger.info("Initializing Random Forest (n_estimators=100, max_depth=None, random_state=42, n_jobs=2)")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2  # CPU-only, parallel on 2 cores
    )

    logger.info("Training model...")
    model.fit(X_train, y_train)

    logger.info("Evaluating on test set...")
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    logger.info(f"Test Metrics - MSE: {mse:.4f}, R²: {r2:.4f}, MAE: {mae:.4f}")

    return model, {'mse': mse, 'r2': r2, 'mae': mae}

def run_cross_validation(X, y, logger):
    """
    Perform k-fold cross-validation with stratified splitting.
    
    Since Random Forest is a regression model, we bin the target variable
    to create discrete classes for stratification, ensuring the distribution
    of the target is preserved across folds.
    
    Returns:
        cv_scores: List of R² scores for each fold.
    """
    logger.info("Starting k-fold Cross-Validation (Stratified, k=5)")
    
    # Create stratification bins based on fidelity_loss (target y)
    # We use 5 bins to match k=5 folds, ensuring each fold has a representative
    # distribution of the target variable.
    n_splits = 5
    try:
        # Create bins based on quantiles to ensure balanced splits
        bins = np.quantile(y, np.linspace(0, 1, n_splits + 1))
        # Ensure unique bins if data is too uniform
        if len(np.unique(bins)) < 2:
            logger.warning("Target distribution too uniform for quantile binning; using uniform bins.")
            bins = np.linspace(y.min(), y.max(), n_splits + 1)
        
        # Assign stratification labels
        stratify_labels = np.digitize(y, bins)
        
        # Ensure all labels are present (handle edge case where some bins are empty)
        unique_labels = np.unique(stratify_labels)
        if len(unique_labels) < n_splits:
            logger.warning(f"Only {len(unique_labels)} unique stratification labels found; adjusting n_splits.")
            # Fallback to simple KFold if stratification fails
            cv = StratifiedKFold(n_splits=len(unique_labels), shuffle=True, random_state=42)
        else:
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    except Exception as e:
        logger.warning(f"Stratification failed ({e}); falling back to standard KFold.")
        from sklearn.model_selection import KFold
        cv = KFold(n_splits=n_splits, shuffle=True, random_state=42)

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=None,
        random_state=42,
        n_jobs=2
    )

    # Perform cross-validation
    # We use R² as the scoring metric
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='r2', n_jobs=2)
    
    logger.info(f"Cross-Validation R² Scores: {cv_scores}")
    logger.info(f"Mean CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    return cv_scores.tolist()

def save_results(model, metrics, results_path, logger):
    """Serialize trained model and metrics to disk."""
    logger.info(f"Saving model artifact to {results_path}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    
    # Save model using pickle
    with open(results_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Model saved successfully to {results_path}")
    
    # Save metrics to a separate JSON file for easy inspection
    metrics_path = results_path.replace('.pkl', '_metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Test metrics saved to {metrics_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Train Random Forest model for fidelity loss prediction")
    parser.add_argument(
        "--features",
        type=str,
        default=str(PROJECT_ROOT / "data" / "processed" / "features.json"),
        help="Path to features JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "results" / "model.pkl"),
        help="Path to save model artifact"
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=str(PROJECT_ROOT / "logs"),
        help="Directory for log files"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    os.makedirs(args.log_dir, exist_ok=True)
    logger = setup_logging()
    logger.info("=== Starting Model Training (T027c) & Cross-Validation (T028) ===")

    try:
        # Load features
        data = load_features(args.features)
        
        # Prepare data
        X, y, sample_ids = prepare_data(data)
        
        # Train and evaluate
        model, metrics = train_and_evaluate(X, y, logger)
        
        # Run Cross-Validation (T028)
        cv_scores = run_cross_validation(X, y, logger)
        
        # Augment metrics with CV results
        metrics['cv_scores'] = cv_scores
        metrics['cv_mean_r2'] = float(np.mean(cv_scores))
        metrics['cv_std_r2'] = float(np.std(cv_scores))
        
        # Save model artifact (T027c specific)
        save_results(model, metrics, args.output, logger)
        
        logger.info("=== Training and Validation Complete ===")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())