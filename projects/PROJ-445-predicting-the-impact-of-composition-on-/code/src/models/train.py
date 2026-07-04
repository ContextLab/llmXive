import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, GridSearchCV, KFold
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Add project root to path if running as script
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(project_root))

from src.utils.manifest_manager import load_manifest, save_manifest, register_artifact, compute_file_hash
from src.data.split import load_processed_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_split_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load train/test splits from processed data artifacts.
    Returns: X_train, X_test, y_train, y_test
    """
    logger.info(f"Loading split data from {data_dir}")
    
    # Load processed data
    train_df = pd.read_csv(data_dir / "train.csv")
    test_df = pd.read_csv(data_dir / "test.csv")
    
    # Separate features and target
    # Assuming 'Tg' is the target column
    feature_cols = [col for col in train_df.columns if col != 'Tg']
    
    X_train = train_df[feature_cols]
    y_train = train_df['Tg']
    X_test = test_df[feature_cols]
    y_test = test_df['Tg']
    
    logger.info(f"Loaded {len(X_train)} training samples, {len(X_test)} test samples")
    logger.info(f"Features: {feature_cols}")
    
    return X_train, X_test, y_train, y_test

def train_linear_baseline(X_train: pd.DataFrame, X_test: pd.DataFrame, 
                          y_train: pd.Series, y_test: pd.Series) -> LinearRegression:
    """
    Train a Linear Regression baseline model.
    """
    logger.info("Training Linear Regression baseline...")
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    
    logger.info(f"Linear Baseline - Train RMSE: {train_rmse:.2f}, Test RMSE: {test_rmse:.2f}")
    logger.info(f"Linear Baseline - Train R²: {train_r2:.3f}, Test R²: {test_r2:.3f}")
    
    return model

def train_gradient_boosting(X_train: pd.DataFrame, X_test: pd.DataFrame,
                            y_train: pd.Series, y_test: pd.Series,
                            cv_folds: int = 5) -> GradientBoostingRegressor:
    """
    Train a Gradient Boosting Regressor with hyperparameter tuning.
    Search space is constrained to meet 6-hour CI limit.
    """
    logger.info("Training Gradient Boosting Regressor with hyperparameter tuning...")
    
    # Constrained hyperparameter search space to ensure completion within 6 hours
    # on free-tier CI (2 CPU, ~7GB RAM)
    param_grid = {
        'n_estimators': [50, 100],  # Limited to ensure speed
        'max_depth': [3, 5],        # Shallow trees for speed
        'learning_rate': [0.05, 0.1],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2],
        'subsample': [0.8, 1.0]
    }
    
    # Use KFold with fixed random state for reproducibility
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
    
    # Grid search with constrained resources
    # Using n_jobs=1 to avoid memory issues on free-tier CI
    grid_search = GridSearchCV(
        estimator=GradientBoostingRegressor(random_state=42),
        param_grid=param_grid,
        cv=cv,
        scoring='neg_root_mean_squared_error',
        n_jobs=1,  # CPU-only, no parallelism to save memory
        verbose=1,
        refit=True
    )
    
    logger.info("Starting GridSearchCV...")
    grid_search.fit(X_train, y_train)
    
    logger.info(f"Best parameters: {grid_search.best_params_}")
    logger.info(f"Best CV score: {-grid_search.best_score_:.2f}")
    
    best_model = grid_search.best_estimator_
    
    # Evaluate on test set
    y_pred_test = best_model.predict(X_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    test_r2 = r2_score(y_test, y_pred_test)
    
    logger.info(f"Gradient Boosting - Test RMSE: {test_rmse:.2f}")
    logger.info(f"Gradient Boosting - Test R²: {test_r2:.3f}")
    
    return best_model, grid_search.best_params_

def save_models(models: Dict[str, any], output_dir: Path, manifest_path: Path) -> None:
    """
    Save trained models and update manifest with checksums.
    """
    logger.info(f"Saving models to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for name, model in models.items():
        model_path = output_dir / f"{name}.joblib"
        joblib.dump(model, model_path)
        logger.info(f"Saved {name} to {model_path}")
        
        # Register in manifest
        register_artifact(
            manifest_path=manifest_path,
            artifact_path=str(model_path),
            artifact_type="model",
            description=f"Trained {name} model"
        )

def main():
    """
    Main entry point for model training with hyperparameter tuning.
    """
    # Paths
    project_root = Path(__file__).resolve().parents[3]
    data_dir = project_root / "data" / "processed"
    model_dir = project_root / "data" / "models"
    manifest_path = project_root / "state" / "manifest.json"
    
    # Ensure directories exist
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    X_train, X_test, y_train, y_test = load_split_data(data_dir)
    
    # Train models
    linear_model = train_linear_baseline(X_train, X_test, y_train, y_test)
    gb_model, best_params = train_gradient_boosting(X_train, X_test, y_train, y_test)
    
    # Save models
    models = {
        "linear_baseline": linear_model,
        "gradient_boosting": gb_model
    }
    save_models(models, model_dir, manifest_path)
    
    # Save best parameters to artifact
    params_path = model_dir / "best_params.json"
    with open(params_path, 'w') as f:
        json.dump(best_params, f, indent=2)
    
    register_artifact(
        manifest_path=manifest_path,
        artifact_path=str(params_path),
        artifact_type="config",
        description="Best hyperparameters from GridSearchCV"
    )
    
    logger.info("Training complete. Models saved.")
    
    return linear_model, gb_model, best_params

if __name__ == "__main__":
    main()