"""
Model training logic.
Implements Random Forest and SVM with grid search.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
from config import RANDOM_SEED

def train_random_forest_grid_search(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    param_grid: Dict[str, list],
    random_seed: int = RANDOM_SEED,
    output_dir: Optional[Path] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Random Forest model with Grid Search.
    
    Args:
        X_train: Training features.
        y_train: Training targets.
        X_val: Validation features.
        y_val: Validation targets.
        param_grid: Grid of hyperparameters.
        random_seed: Random seed for reproducibility.
        output_dir: Directory to save model and metrics.
        
    Returns:
        Tuple of (best_model, metrics_dict)
    """
    rf = RandomForestRegressor(random_state=random_seed, n_jobs=-1)
    
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=3,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Evaluate on validation set
    y_pred = best_model.predict(X_val)
    r2 = r2_score(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    mae = mean_absolute_error(y_val, y_pred)
    
    metrics = {
        "r2": float(r2),
        "rmse": float(rmse),
        "mae": float(mae),
        "best_params": best_params
    }
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / "rf_best_model.pkl"
        metrics_path = output_dir / "rf_metrics.json"
        
        joblib.dump(best_model, model_path)
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    return best_model, metrics
