"""
Cross-Validation Implementation for User Story 3.

Implements k-fold cross-validation on composition/temperature data points
to assess model robustness (FR-005).

This module performs the core logic for T029 (Implementation) and supports
T030 (Metrics Reporting). It loads pre-computed interaction terms from
data/processed/interaction_terms.csv, performs k-fold splitting, trains
linear regression models on each fold, and evaluates performance metrics.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error

from code.config import PROCESSED_PATH, get_logger
from code.models.regression import load_interaction_terms
from code.errors import DataLoadError

logger = get_logger(__name__)


def load_cv_data(input_path: Optional[Path] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load interaction terms and target variables for cross-validation.
    
    Args:
        input_path: Path to the interaction terms CSV. Defaults to 
                   data/processed/interaction_terms.csv if None.
                    
    Returns:
        Tuple of (features, targets) as numpy arrays.
        
    Raises:
        DataLoadError: If the file cannot be loaded or is malformed.
    """
    if input_path is None:
        input_path = PROCESSED_PATH / "interaction_terms.csv"
        
    if not input_path.exists():
        raise DataLoadError(f"Input file not found: {input_path}")
        
    try:
        df = pd.read_csv(input_path)
        
        # Identify target column (typically 'segregation_energy' or similar)
        # Assuming the last column is the target based on T021b logic
        feature_cols = [col for col in df.columns if col != 'segregation_energy']
        target_col = 'segregation_energy'
        
        if target_col not in df.columns:
            # Fallback: use the last column as target
            target_col = df.columns[-1]
            feature_cols = [col for col in df.columns if col != target_col]
        
        logger.info(f"Loading features: {feature_cols}, target: {target_col}")
        
        features = df[feature_cols].values
        targets = df[target_col].values
        
        # Handle missing values
        if np.isnan(features).any() or np.isnan(targets).any():
            logger.warning("NaN values detected. Dropping incomplete rows.")
            mask = ~np.isnan(features).any(axis=1) & ~np.isnan(targets)
            features = features[mask]
            targets = targets[mask]
            
        if len(features) == 0:
            raise DataLoadError("No valid data rows after cleaning.")
            
        logger.info(f"Loaded {len(features)} data points for cross-validation.")
        return features, targets
        
    except Exception as e:
        raise DataLoadError(f"Failed to load interaction terms: {e}")


def run_cross_validation(
    features: np.ndarray, 
    targets: np.ndarray, 
    k: int = 5, 
    random_state: int = 42
) -> List[Dict[str, float]]:
    """
    Perform k-fold cross-validation on the provided data.
    
    Args:
        features: Input feature matrix (N, M).
        targets: Target vector (N,).
        k: Number of folds.
        random_state: Random seed for reproducibility.
        
    Returns:
        List of dictionaries containing 'fold', 'r2', and 'mse' for each fold.
    """
    logger.info(f"Starting {k}-fold cross-validation on {len(features)} samples.")
    
    if len(features) < k:
        logger.warning(f"Sample size ({len(features)}) is less than k ({k}). "
                     "Adjusting k to sample size.")
        k = len(features)
        
    if k < 2:
        raise ValueError("Need at least 2 samples to perform cross-validation.")

    kf = KFold(n_splits=k, shuffle=True, random_state=random_state)
    fold_results = []

    for fold_idx, (train_index, test_index) in enumerate(kf.split(features)):
        X_train, X_test = features[train_index], features[test_index]
        y_train, y_test = targets[train_index], targets[test_index]

        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Predict and evaluate
        y_pred = model.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)

        fold_results.append({
            "fold": fold_idx + 1,
            "r2": float(r2),
            "mse": float(mse)
        })
        
        logger.debug(f"Fold {fold_idx + 1}: R²={r2:.4f}, MSE={mse:.6f}")

    logger.info(f"Cross-validation completed. {k} folds processed.")
    return fold_results


def calculate_cv_metrics(fold_results: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calculate aggregate metrics (mean, std dev) from fold results.
    
    Args:
        fold_results: List of fold result dictionaries.
        
    Returns:
        Dictionary with mean_r2, std_r2, mean_mse, std_mse.
    """
    if not fold_results:
        return {
            "mean_r2": 0.0,
            "std_r2": 0.0,
            "mean_mse": 0.0,
            "std_mse": 0.0
        }

    r2_scores = [f['r2'] for f in fold_results]
    mse_scores = [f['mse'] for f in fold_results]

    mean_r2 = float(np.mean(r2_scores))
    std_r2 = float(np.std(r2_scores))
    mean_mse = float(np.mean(mse_scores))
    std_mse = float(np.std(mse_scores))

    logger.info(f"Mean R²: {mean_r2:.4f}, Std Dev: {std_r2:.4f}")
    logger.info(f"Mean MSE: {mean_mse:.6f}, Std Dev: {std_mse:.6f}")

    # Flag high variance
    if std_r2 > 0.05:
        logger.warning(f"High variance detected in R² scores (std={std_r2:.4f} > 0.05). "
                     "Model may be unstable.")

    return {
        "mean_r2": mean_r2,
        "std_r2": std_r2,
        "mean_mse": mean_mse,
        "std_mse": std_mse
    }


def evaluate_transferability(
    train_features: np.ndarray,
    train_targets: np.ndarray,
    test_features: np.ndarray,
    test_targets: np.ndarray
) -> Optional[float]:
    """
    Evaluate model transferability by training on one system and testing on another.
    
    This implements the logic for T031 (Transferability Check).
    
    Args:
        train_features: Features for training system.
        train_targets: Targets for training system.
        test_features: Features for testing system.
        test_targets: Targets for testing system.
        
    Returns:
        R² score on the test set, or None if evaluation fails.
    """
    if len(train_features) == 0 or len(test_features) == 0:
        logger.warning("Empty dataset provided for transferability check.")
        return None

    try:
        model = LinearRegression()
        model.fit(train_features, train_targets)
        y_pred = model.predict(test_features)
        r2 = r2_score(test_targets, y_pred)
        logger.info(f"Transferability R²: {r2:.4f}")
        return float(r2)
    except Exception as e:
        logger.error(f"Transferability evaluation failed: {e}")
        return None


def save_cv_results(
    fold_results: List[Dict[str, float]], 
    metrics: Dict[str, float], 
    output_path: Path
):
    """
    Save cross-validation results to JSON.
    
    Args:
        fold_results: List of fold details.
        metrics: Aggregate metrics.
        output_path: Path to save the JSON file.
    """
    output_data = {
        "k_folds": len(fold_results),
        "metrics": metrics,
        "fold_details": fold_results,
        "status": "high_variance" if metrics['std_r2'] > 0.05 else "success",
        "timestamp": str(pd.Timestamp.now())
    }
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Cross-validation results saved to {output_path}")


def main():
    """
    Main entry point for T029-Exec and T030-Exec.
    Loads interaction terms, runs CV, calculates metrics, and saves results.
    """
    logger.info("Starting Cross-Validation Execution (T029/T030).")
    
    # Load data
    try:
        features, targets = load_cv_data()
    except DataLoadError as e:
        logger.error(f"Data loading failed: {e}")
        # Create a minimal error output
        output_path = PROCESSED_PATH / "cv_metrics.json"
        save_cv_results([], {"mean_r2": 0.0, "std_r2": 0.0, "mean_mse": 0.0, "std_mse": 0.0}, output_path)
        return
    except Exception as e:
        logger.error(f"Unexpected error during data loading: {e}")
        return

    if features is None or targets is None or len(features) == 0:
        logger.error("No valid data available for cross-validation.")
        return

    # Run CV
    fold_results = run_cross_validation(features, targets, k=5)

    if not fold_results:
        logger.warning("No folds were generated.")
        return

    # Calculate Metrics
    metrics = calculate_cv_metrics(fold_results)

    # Save Results
    output_path = PROCESSED_PATH / "cv_metrics.json"
    save_cv_results(fold_results, metrics, output_path)

    logger.info("Cross-Validation Execution completed successfully.")


if __name__ == "__main__":
    main()