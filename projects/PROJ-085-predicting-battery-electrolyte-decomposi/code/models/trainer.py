"""
Model Training Module.

Trains a Random Forest Regressor with 5-fold Cross-Validation and GridSearchCV.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

# Add project root to path
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_data_dir, get_project_root, get_seed
from utils.logging_config import get_logger

logger = get_logger(__name__)


def load_processed_features(csv_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the processed features CSV.
    """
    if csv_path is None:
        data_dir = get_data_dir()
        csv_path = data_dir / "processed" / "electrolyte_features.csv"
        
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed features file not found at {path}")
        
    return pd.read_csv(csv_path)


def filter_bin_data(df: pd.DataFrame, bin_type: str = "low") -> pd.DataFrame:
    """
    Filter data based on potential bins.
    
    Args:
        df: Input DataFrame.
        bin_type: 'low' (0-2V) or 'high' (4V).
        
    Returns:
        Filtered DataFrame.
    """
    if 'potential_v' not in df.columns:
        raise ValueError("Column 'potential_v' not found in DataFrame")
        
    if bin_type == "low":
        # 0V and 2V
      return df[df['potential_v'].isin([0, 2])]
    elif bin_type == "high":
        # 4V (mapping spec's 3-5V to 4V)
        return df[df['potential_v'] == 4]
    else:
        return df


def train_random_forest(X: np.ndarray, y: np.ndarray, n_estimators_range: List[int], max_depth_range: List[int]) -> Tuple[Any, Dict[str, Any]]:
    """
    Train a Random Forest with GridSearchCV.
    
    Args:
        X: Features.
        y: Target.
        n_estimators_range: List of n_estimators to search.
        max_depth_range: List of max_depth to search.
        
    Returns:
        Tuple of (Best Model, Best Params)
    """
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import GridSearchCV, cross_val_score
    from sklearn.metrics import r2_score, mean_absolute_error
    
    param_grid = {
        'n_estimators': n_estimators_range,
        'max_depth': max_depth_range
    }
    
    rf = RandomForestRegressor(random_state=get_seed())
    
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=5,
        scoring='r2',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X, y)
    
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    
    # Calculate CV score
    cv_scores = cross_val_score(best_model, X, y, cv=5, scoring='r2')
    
    # Final evaluation on the split data (approximate)
    # For a real split, we would use train/test, but here we use CV scores as the metric
    
    metrics = {
        'best_params': best_params,
        'mean_cv_r2': float(np.mean(cv_scores)),
        'std_cv_r2': float(np.std(cv_scores)),
        'cv_scores': cv_scores.tolist()
    }
    
    return best_model, metrics


def save_model_artifacts(model: Any, metrics: Dict[str, Any], output_path: str, feature_names: List[str]):
    """
    Save the model and metrics to disk.
    """
    import joblib
    
    model_path = Path(output_path).parent / "random_forest_model.joblib"
    metrics_path = Path(output_path)
    
    joblib.dump(model, model_path)
    
    # Prepare JSON content
    json_content = {
        'model_path': str(model_path),
        'metrics': metrics,
        'feature_names': feature_names,
        'timestamp': str(pd.Timestamp.now())
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(json_content, f, indent=2)
        
    logger.info(f"Model saved to {model_path}")
    logger.info(f"Metrics saved to {metrics_path}")


def run_trainer_pipeline(bin_type: str = "low", output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full training pipeline for a specific bin.
    """
    # Load data
    df = load_processed_features()
    
    # Filter
    df_bin = filter_bin_data(df, bin_type)
    
    if df_bin.empty:
        logger.warning(f"No data found for bin {bin_type}")
        return {}
        
    # Prepare features and target
    # Assuming 'e_decomp_ev' is the target
    target_col = 'e_decomp_ev'
    feature_cols = [c for c in df_bin.columns if c not in ['molecule_id', 'potential_v', target_col, 'is_metallic']]
    
    # Drop rows with NaN in features or target
    df_clean = df_bin[feature_cols + [target_col]].dropna()
    
    if df_clean.empty:
        logger.warning("Cleaned data is empty.")
        return {}
        
    X = df_clean[feature_cols].values
    y = df_clean[target_col].values
    
    # Train
    n_estimators_range = [50, 100, 200]
    max_depth_range = [10, 20, None]
    
    logger.info(f"Training Random Forest for bin: {bin_type}")
    model, metrics = train_random_forest(X, y, n_estimators_range, max_depth_range)
    
    # Save
    if output_path is None:
        data_dir = get_data_dir()
        output_path = str(data_dir / "processed" / f"model_run_{bin_type}.json")
        
    save_model_artifacts(model, metrics, output_path, feature_cols)
    
    return metrics


if __name__ == "__main__":
    # Run for both bins
    print("Running Trainer Pipeline...")
    run_trainer_pipeline("low")
    run_trainer_pipeline("high")
