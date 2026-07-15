"""
Train a Gradient Boosting model for Metallic Glass Tg prediction using LOFO CV.

Implements Leave-One-Family-Out cross-validation as per FR-003.
Performs hyperparameter grid search and saves model artifacts.
"""
import os
import sys
import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import warnings

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_validate, LeaveOneGroupOut
from sklearn.metrics import make_scorer, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler

# Project imports
from config.config import get_config, Config
from descriptors import process_dataframe, compute_descriptors
from resource_monitor import resource_monitor, ResourceLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CONFIG_PATH = Path("code/config/config.yaml")
INPUT_DATA_PATH = Path("data/processed/cleaned_mg.csv")
MODEL_OUTPUT_DIR = Path("artifacts/models")
METRICS_OUTPUT_DIR = Path("artifacts/metrics")
DESCRIPTOR_OUTPUT_PATH = Path("data/processed/descriptors.csv")

# Hyperparameter grid for search (<=10 combos as per FR-003)
PARAM_GRID = [
    {"n_estimators": 50, "max_depth": 3, "learning_rate": 0.1},
    {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.1},
    {"n_estimators": 100, "max_depth": 4, "learning_rate": 0.1},
    {"n_estimators": 100, "max_depth": 5, "learning_rate": 0.1},
    {"n_estimators": 100, "max_depth": 3, "learning_rate": 0.05},
    {"n_estimators": 150, "max_depth": 3, "learning_rate": 0.1},
    {"n_estimators": 100, "max_depth": 4, "learning_rate": 0.05},
    {"n_estimators": 200, "max_depth": 3, "learning_rate": 0.1},
]

def load_prepared_data() -> pd.DataFrame:
    """Load cleaned data and compute descriptors."""
    if not INPUT_DATA_PATH.exists():
        raise FileNotFoundError(f"Input data not found at {INPUT_DATA_PATH}. "
                                "Run T014 (ingest) first.")
    
    logger.info(f"Loading data from {INPUT_DATA_PATH}")
    df = pd.read_csv(INPUT_DATA_PATH)
    
    # Ensure target column exists
    if 'Tg' not in df.columns:
        raise ValueError("Target column 'Tg' not found in dataset.")
    
    # Compute descriptors using existing API
    logger.info("Computing atomic descriptors...")
    try:
        # process_dataframe expects the raw dataframe and returns processed one
        # It uses compute_descriptors internally
        df_processed = process_dataframe(df)
    except Exception as e:
        logger.error(f"Descriptor computation failed: {e}")
        raise
    
    # Save descriptors for downstream tasks (T033, T035)
    df_processed.to_csv(DESCRIPTOR_OUTPUT_PATH, index=False)
    logger.info(f"Descriptors saved to {DESCRIPTOR_OUTPUT_PATH}")
    
    return df_processed

def get_family_groups(df: pd.DataFrame) -> List[str]:
    """Extract unique family labels for LOFO CV."""
    if 'family' not in df.columns:
        # Fallback: try to infer from composition if 'family' missing
        # But spec implies 'family' should exist from ingestion
        raise ValueError("Column 'family' required for LOFO CV not found.")
    return df['family'].unique().tolist()

def train_and_evaluate(
    X: np.ndarray, 
    y: np.ndarray, 
    groups: np.ndarray, 
    params: Dict[str, Any]
) -> Dict[str, float]:
    """Train a single model and return CV metrics."""
    model = GradientBoostingRegressor(**params)
    cv = LeaveOneGroupOut()
    
    # Use r2 and mae scorers
    scoring = {
        'r2': 'r2',
        'neg_mae': 'neg_mean_absolute_error'
    }
    
    # Perform LOFO CV
    scores = cross_validate(
        model, X, y, cv=cv, groups=groups, scoring=scoring,
        return_train_score=False, n_jobs=1
    )
    
    return {
        'r2_mean': float(np.mean(scores['test_r2'])),
        'r2_std': float(np.std(scores['test_r2'])),
        'mae_mean': float(-np.mean(scores['test_neg_mae'])),
        'mae_std': float(np.std(scores['test_neg_mae']))
    }

def grid_search_lofo(df: pd.DataFrame) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """Perform grid search with LOFO CV to find best hyperparameters."""
    # Prepare features and target
    feature_cols = [c for c in df.columns if c not in ['Tg', 'family', 'composition', 'alloy_id']]
    X = df[feature_cols].values
    y = df['Tg'].values
    groups = df['family'].values
    
    logger.info(f"Features for training: {feature_cols}")
    logger.info(f"Number of families (LOFO folds): {len(np.unique(groups))}")
    
    results = []
    
    for params in PARAM_GRID:
        logger.info(f"Evaluating params: {params}")
        metrics = train_and_evaluate(X, y, groups, params)
        results.append({**params, **metrics})
        logger.info(f"  R2: {metrics['r2_mean']:.4f} (+/- {metrics['r2_std']:.4f})")
    
    # Sort by R2 descending
    results.sort(key=lambda x: x['r2_mean'], reverse=True)
    best_result = results[0]
    best_params = {k: v for k, v in best_result.items() if k in PARAM_GRID[0].keys()}
    
    logger.info(f"Best params: {best_params}")
    logger.info(f"Best R2: {best_result['r2_mean']:.4f}")
    
    return best_params, best_result

def save_artifacts(
    df: pd.DataFrame, 
    best_params: Dict[str, Any], 
    best_metrics: Dict[str, float],
    feature_importances: Optional[np.ndarray] = None
) -> None:
    """Save model and metrics to artifacts directory."""
    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Re-train final model on full data with best params
    feature_cols = [c for c in df.columns if c not in ['Tg', 'family', 'composition', 'alloy_id']]
    X = df[feature_cols].values
    y = df['Tg'].values
    
    final_model = GradientBoostingRegressor(**best_params)
    final_model.fit(X, y)
    
    # Save model
    model_path = MODEL_OUTPUT_DIR / "best_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': final_model,
            'feature_cols': feature_cols,
            'params': best_params
        }, f)
    logger.info(f"Model saved to {model_path}")
    
    # Prepare metrics
    metrics_data = {
        'r2_mean': best_metrics['r2_mean'],
        'r2_std': best_metrics['r2_std'],
        'mae_mean': best_metrics['mae_mean'],
        'mae_std': best_metrics['mae_std'],
        'hyperparameters': best_params,
        'feature_importances': (
            final_model.feature_importances_.tolist() 
            if feature_importances is None 
            else feature_importances.tolist()
        ),
        'feature_names': feature_cols,
        'n_samples': len(df),
        'n_families': len(df['family'].unique())
    }
    
    # Save metrics
    metrics_path = METRICS_OUTPUT_DIR / "training_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

def main() -> int:
    """Main entry point for training pipeline."""
    logger.info("Starting T022: Model Training with LOFO CV")
    
    try:
        # Load data and compute descriptors
        df = load_prepared_data()
        
        # Perform grid search with LOFO
        best_params, best_metrics = grid_search_lofo(df)
        
        # Save artifacts
        save_artifacts(df, best_params, best_metrics)
        
        logger.info("Training completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
