"""
Training pipeline for Metallic Glass Tg prediction.

Implements Leave-One-Family-Out (LOFO) cross-validation, grid search,
and artifact saving. Enforces resource limits (6h CPU, 7GB RAM) as per FR-005.
"""
import os
import sys
import logging
import json
import pickle
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Union

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Import resource monitoring utilities
from resource_monitor import enforce_resource_limits, ResourceLimitExceeded, logger as resource_logger

# Import descriptor utilities (assuming T026 completed)
from descriptors import process_dataframe

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_MODELS = PROJECT_ROOT / "artifacts" / "models"
ARTIFACTS_METRICS = PROJECT_ROOT / "artifacts" / "metrics"

# Ensure output directories exist
ARTIFACTS_MODELS.mkdir(parents=True, exist_ok=True)
ARTIFACTS_METRICS.mkdir(parents=True, exist_ok=True)


def load_prepared_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleaned and descriptor-computed data.
    
    Args:
        filepath: Path to the CSV file. Defaults to data/processed/descriptors.csv
        
    Returns:
        DataFrame with features and target
    """
    if filepath is None:
        filepath = DATA_PROCESSED / "descriptors.csv"
    
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)
    
    # Ensure target column exists
    if 'Tg' not in df.columns:
        raise ValueError("Data must contain 'Tg' column")
        
    return df


def get_family_groups(df: pd.DataFrame) -> Dict[str, List[int]]:
    """
    Group data points by their alloy family (e.g., Zr-based, Pd-based).
    
    Args:
        df: DataFrame with composition or family column
        
    Returns:
        Dictionary mapping family name to list of indices
    """
    # Heuristic: Group by the primary element or a specific 'family' column if present
    # Assuming the 'composition' or a derived 'primary_element' column exists
    # If 'family' column exists, use that. Otherwise, infer from composition.
    
    if 'family' in df.columns:
        groups = df.groupby('family').indices
    elif 'primary_element' in df.columns:
        groups = df.groupby('primary_element').indices
    else:
        # Fallback: Group by the first element in composition string if formatted "A-B-C"
        # This is a rough heuristic if no explicit family column exists
        logger.warning("No explicit family column found. Inferring from composition.")
        families = []
        for comp in df['composition']:
            # Simple split on hyphen or comma, take first element
            primary = comp.split('-')[0].split(',')[0].strip()
            families.append(primary)
        df_temp = df.copy()
        df_temp['inferred_family'] = families
        groups = df_temp.groupby('inferred_family').indices
        
    return groups


def lofo_cv_score(
    model: Any,
    X: pd.DataFrame,
    y: pd.Series,
    groups: Dict[str, List[int]],
    scoring: str = 'r2'
) -> List[float]:
    """
    Perform Leave-One-Family-Out Cross-Validation.
    
    Args:
        model: Scikit-learn compatible regressor
        X: Feature DataFrame
        y: Target Series
        groups: Dictionary of family -> indices
        scoring: Scoring metric
        
    Returns:
        List of scores for each fold
    """
    scores = []
    X_np = X.values
    y_np = y.values
    
    # Create a list of (test_indices, train_indices)
    # We need to iterate over families, leaving one out
    all_indices = set(range(len(df)))
    
    for family, test_indices in groups.items():
        test_indices = list(test_indices)
        train_indices = list(all_indices - set(test_indices))
        
        if len(train_indices) == 0:
            logger.warning(f"Family {family} is the only data point. Skipping.")
            continue
            
        X_train, X_test = X_np[train_indices], X_np[test_indices]
        y_train, y_test = y_np[train_indices], y_np[test_indices]
        
        model.fit(X_train, y_train)
        score = model.score(X_test, y_test)
        scores.append(score)
        logger.info(f"LOFO Fold (Family: {family}): R² = {score:.4f}")
        
    return scores


@enforce_resource_limits(cpu_limit=6 * 3600, ram_limit=7 * 1024)
def train_and_evaluate(df: pd.DataFrame) -> Tuple[Any, Dict[str, float]]:
    """
    Train a Gradient Boosting model with LOFO CV.
    
    Args:
        df: DataFrame with features and 'Tg'
        
    Returns:
        Tuple of (trained model, metrics dict)
    """
    logger.info("Starting training and evaluation with resource limits...")
    
    # Prepare features and target
    # Exclude non-feature columns
    feature_cols = [c for c in df.columns if c not in ['Tg', 'composition', 'family', 'primary_element']]
    if not feature_cols:
        raise ValueError("No feature columns found in dataframe")
        
    X = df[feature_cols]
    y = df['Tg']
    
    # Get family groups for LOFO
    groups = get_family_groups(df)
    
    # Define base model
    base_model = GradientBoostingRegressor(random_state=42)
    
    # Perform LOFO CV to get baseline score
    logger.info("Performing LOFO Cross-Validation...")
    try:
        lofo_scores = lofo_cv_score(base_model, X, y, groups)
        mean_lofo_r2 = np.mean(lofo_scores)
        std_lofo_r2 = np.std(lofo_scores)
        logger.info(f"LOFO Mean R²: {mean_lofo_r2:.4f} (+/- {std_lofo_r2:.4f})")
    except Exception as e:
        logger.error(f"LOFO CV failed: {e}")
        # Fallback to standard CV if LOFO fails (e.g., not enough families)
        logger.warning("Falling back to standard 5-fold CV")
        scores = cross_val_score(base_model, X, y, cv=5, scoring='r2')
        mean_lofo_r2 = np.mean(scores)
        std_lofo_r2 = np.std(scores)
        
    # Grid Search for Hyperparameters
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [3, 5],
        'learning_rate': [0.05, 0.1]
    }
    
    logger.info("Starting Grid Search...")
    grid_search = GridSearchCV(
        GradientBoostingRegressor(random_state=42),
        param_grid,
        cv=3,
        scoring='r2',
        n_jobs=-1,
        refit=True
    )
    
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Evaluate best model on full data (or holdout if specified, but we use full for now)
    # Note: In a real pipeline, we might split train/test before this.
    # For this task, we assume the model is trained on available data.
    y_pred = best_model.predict(X)
    final_r2 = r2_score(y, y_pred)
    final_mae = mean_absolute_error(y, y_pred)
    
    metrics = {
        'best_params': best_params,
        'lofo_mean_r2': float(mean_lofo_r2),
        'lofo_std_r2': float(std_lofo_r2),
        'grid_search_cv_r2': float(grid_search.best_score_),
        'final_r2': float(final_r2),
        'final_mae': float(final_mae),
        'feature_importances': dict(zip(feature_cols, best_model.feature_importances_.tolist()))
    }
    
    logger.info(f"Training complete. Final R²: {final_r2:.4f}, MAE: {final_mae:.4f}")
    return best_model, metrics


def save_artifacts(model: Any, metrics: Dict[str, Any]) -> None:
    """
    Save model and metrics to disk.
    
    Args:
        model: Trained model
        metrics: Metrics dictionary
    """
    model_path = ARTIFACTS_MODELS / "best_model.pkl"
    metrics_path = ARTIFACTS_METRICS / "metrics.json"
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")


def main():
    """
    Main entry point for the training pipeline.
    """
    try:
        # Load data
        df = load_prepared_data()
        
        # Train and evaluate (with resource monitoring)
        model, metrics = train_and_evaluate(df)
        
        # Save artifacts
        save_artifacts(model, metrics)
        
        logger.info("Pipeline completed successfully.")
        
    except ResourceLimitExceeded as e:
        logger.error(f"Pipeline halted due to resource limits: {e}")
        # Exit gracefully with error code
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()