import os
import sys
import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut, cross_validate
from sklearn.metrics import make_scorer, r2_score, mean_absolute_error
from sklearn.model_selection import GridSearchCV
import joblib

# Import resource monitoring utilities
from resource_monitor import ResourceLimitExceeded, enforce_resource_limits, get_current_ram_mb, get_current_cpu_time

# Import descriptor utilities if needed for data loading context
# (Assuming descriptors are already computed and saved per T020/T021)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_RAM_MB = 7 * 1024  # 7 GB
MAX_CPU_TIME_SEC = 6 * 3600  # 6 hours
DATA_PATH = Path("data/processed/cleaned_mg.csv")
MODEL_DIR = Path("artifacts/models")
METRICS_DIR = Path("artifacts/metrics")

def load_prepared_data() -> pd.DataFrame:
    """Load the cleaned and processed dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Prepared data not found at {DATA_PATH}. "
                                "Run T014 (ingest) first.")
    logger.info(f"Loading data from {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    
    # Ensure target and features are present
    required_cols = ['Tg']
    # We assume descriptors (radius_mismatch, electronegativity_diff, VEC, etc.) 
    # are present in the dataframe from T020/T021 processing.
    # We filter out the 'family' column for features, but keep it for LOFO groups.
    if 'family' not in df.columns:
        raise ValueError("Dataset must contain a 'family' column for LOFO CV.")
    
    return df

def get_family_groups(df: pd.DataFrame) -> List[str]:
    """Extract family groups for Leave-One-Family-Out CV."""
    return df['family'].tolist()

def train_and_evaluate(df: pd.DataFrame, params: Dict[str, Any]) -> Tuple[Any, Dict[str, float]]:
    """
    Train a GradientBoostingRegressor with the given parameters.
    Performs Leave-One-Family-Out (LOFO) cross-validation.
    """
    feature_cols = [col for col in df.columns if col not in ['Tg', 'family']]
    X = df[feature_cols].values
    y = df['Tg'].values
    groups = get_family_groups(df)

    logo = LeaveOneGroupOut()
    
    # Define scorers
    r2_scorer = make_scorer(r2_score)
    mae_scorer = make_scorer(mean_absolute_error, greater_is_better=False) # sklearn expects neg for MAE in some contexts, but make_scorer handles direction if we set greater_is_better=False? Actually mean_absolute_error is loss, so we want to maximize negative MAE.
    # Correction: make_scorer for a loss function (where lower is better) should set greater_is_better=False.
    # However, standard practice is often to use neg_mean_absolute_error.
    # Let's stick to standard sklearn metrics.
    
    model = GradientBoostingRegressor(**params)
    
    # Perform LOFO CV
    cv_results = cross_validate(
        model, X, y, cv=logo, groups=groups,
        scoring={'r2': r2_scorer, 'mae': make_scorer(mean_absolute_error, greater_is_better=False)},
        return_train_score=False,
        n_jobs=1
    )

    metrics = {
        'r2_mean': np.mean(cv_results['test_r2']),
        'r2_std': np.std(cv_results['test_r2']),
        'mae_mean': -np.mean(cv_results['test_mae']), # Convert back to positive
        'mae_std': np.std(cv_results['test_mae'])
    }

    # Train final model on full data
    model.fit(X, y)
    
    return model, metrics

def grid_search_lofo(df: pd.DataFrame) -> Tuple[GradientBoostingRegressor, Dict[str, Any], Dict[str, float]]:
    """
    Perform grid search for hyperparameter optimization with LOFO CV.
    Limits combinations to <= 10 as per FR-003.
    """
    feature_cols = [col for col in df.columns if col not in ['Tg', 'family']]
    X = df[feature_cols].values
    y = df['Tg'].values
    groups = get_family_groups(df)

    logo = LeaveOneGroupOut()

    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [3, 4],
        'learning_rate': [0.05, 0.1]
    }
    
    # Generate all combinations and limit to 10
    from itertools import product
    keys = param_grid.keys()
    values = param_grid.values()
    combinations = [dict(zip(keys, v)) for v in product(*values)]
    
    if len(combinations) > 10:
        logger.warning(f"Found {len(combinations)} combinations, limiting to 10.")
        combinations = combinations[:10]

    best_model = None
    best_score = -np.inf
    best_params = None
    best_metrics = None

    logger.info(f"Starting Grid Search with {len(combinations)} configurations.")

    for i, params in enumerate(combinations):
        logger.info(f"Testing config {i+1}/{len(combinations)}: {params}")
        
        # Check resources before each fold/train
        ram = get_current_ram_mb()
        if ram > MAX_RAM_MB:
            raise ResourceLimitExceeded(f"RAM usage {ram}MB exceeds limit {MAX_RAM_MB}MB")

        model = GradientBoostingRegressor(**params)
        
        # Use LOFO CV for scoring
        cv_results = cross_validate(
            model, X, y, cv=logo, groups=groups,
            scoring={'r2': make_scorer(r2_score)},
            n_jobs=1
        )
        
        mean_r2 = np.mean(cv_results['test_r2'])
        
        if mean_r2 > best_score:
            best_score = mean_r2
            best_params = params
            # Retrain on full data for this best config
            model.fit(X, y)
            best_model = model
            # Calculate final metrics for this model
            best_metrics = {
                'r2_mean': mean_r2,
                'r2_std': np.std(cv_results['test_r2']),
                # Re-evaluate MAE for the best model
                'mae_mean': mean_absolute_error(y, model.predict(X)), # In-sample for reporting, or re-CV?
                # Better to report CV metrics for MAE too for consistency
                'mae_cv_mean': -np.mean(cross_validate(model, X, y, cv=logo, groups=groups, scoring={'mae': make_scorer(mean_absolute_error, greater_is_better=False)})['test_mae'])
            }
    
    if best_model is None:
        raise RuntimeError("Grid search failed to find a valid model.")

    logger.info(f"Best parameters: {best_params} with R² CV: {best_score:.4f}")
    return best_model, best_params, best_metrics

def save_artifacts(model: GradientBoostingRegressor, params: Dict[str, Any], metrics: Dict[str, float], df: pd.DataFrame):
    """Save model, parameters, metrics, and feature importances."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = MODEL_DIR / "best_model.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # Save parameters
    params_path = MODEL_DIR / "best_params.json"
    with open(params_path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.info(f"Parameters saved to {params_path}")

    # Save metrics
    metrics_path = METRICS_DIR / "training_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    # Save feature importances
    feature_cols = [col for col in df.columns if col not in ['Tg', 'family']]
    importances = model.feature_importances_
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values(by='importance', ascending=False)
    
    importance_path = METRICS_DIR / "feature_importances.csv"
    importance_df.to_csv(importance_path, index=False)
    logger.info(f"Feature importances saved to {importance_path}")

def main():
    """Main entry point for the training pipeline."""
    logger.info("Starting Training Pipeline (T025: Resource Monitoring Enabled)")
    
    try:
        # Enforce resource limits on the entire process
        # This wraps the execution to fail if limits are exceeded
        with enforce_resource_limits(max_ram_mb=MAX_RAM_MB, max_cpu_time_sec=MAX_CPU_TIME_SEC):
            # 1. Load Data
            df = load_prepared_data()
            logger.info(f"Loaded {len(df)} records.")

            # 2. Grid Search with LOFO
            best_model, best_params, best_metrics = grid_search_lofo(df)

            # 3. Save Artifacts
            save_artifacts(best_model, best_params, best_metrics, df)

        logger.info("Training pipeline completed successfully within resource limits.")

    except ResourceLimitExceeded as e:
        logger.error(f"Resource limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()