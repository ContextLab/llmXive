import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import logging setup from project utils
from code.logging_config import setup_logging, get_logger
from code.config import get_output_path

# Initialize logger
logger = get_logger(__name__)

def load_aligned_dataset() -> pd.DataFrame:
    """Loads the aligned dataset from data/processed/aligned_dataset.csv."""
    path = Path("data/processed/aligned_dataset.csv")
    if not path.exists():
        raise FileNotFoundError(f"Aligned dataset not found: {path}")
    logger.info(f"Loading aligned dataset from {path}")
    return pd.read_csv(path)

def estimate_runtime_per_sample(df: pd.DataFrame) -> float:
    """
    Estimates runtime per sample based on a calibrated heuristic.
    
    Heuristic derived from typical XGBoost training on CPU:
    - 0.001 seconds per sample for a single fit on a small tree.
    - Adjusted for feature count (columns) if needed, but kept simple for estimation.
    """
    # Base heuristic: 1ms per sample per fit
    base_time_per_sample = 0.001
    
    # Optional: Scale by feature count if dataset is very wide (e.g., > 50 features)
    # This is a rough linear scaling for high-dimensional data
    n_features = len(df.columns)
    if n_features > 50:
        scaling_factor = 1 + (n_features - 50) * 0.01
        base_time_per_sample *= scaling_factor
        
    return base_time_per_sample

def calculate_grid_search_size(grid_config: Dict[str, Any]) -> int:
    """Calculates the total number of grid search combinations."""
    total = 1
    for key, values in grid_config.items():
        if isinstance(values, list):
            total *= len(values)
        elif isinstance(values, int):
            total *= values
        else:
            # Assume it's a single value or invalid, treat as 1
            pass
    return total

def estimate_total_runtime(df: pd.DataFrame, grid_config: Optional[Dict[str, Any]] = None) -> float:
    """
    Estimates total runtime for the XGBoost training phase (T026).
    
    Formula:
    Total Hours = (Samples * TimePerSample * CV_Folds * GridSize) / 3600
    
    Args:
        df: The aligned dataset DataFrame.
        grid_config: Dictionary of hyperparameters and their candidate values.
    
    Returns:
        Estimated runtime in hours.
    """
    samples = len(df)
    per_sample = estimate_runtime_per_sample(df)
    
    # T026 specifies 5-fold outer loop (nested CV)
    cv_folds = 5
    
    base_time_seconds = samples * per_sample * cv_folds
    
    if grid_config:
        grid_size = calculate_grid_search_size(grid_config)
        base_time_seconds *= grid_size
    
    runtime_hours = base_time_seconds / 3600.0
    return runtime_hours

def save_runtime_projection(runtime_hours: float, output_path: str = "outputs/runtime_projection.json"):
    """Saves the runtime projection to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load dataset again to get sample count for the report
    df = load_aligned_dataset()
    
    # Define the grid config used for estimation (matches T026/T047 spec)
    grid_config = {
        "max_depth": [3, 5, 7],
        "learning_rate": [0.01, 0.1, 0.2],
        "n_estimators": [50, 100, 200]
    }
    
    projection_data = {
        "projected_runtime_hours": round(runtime_hours, 4),
        "samples_used": len(df),
        "grid_search_size": calculate_grid_search_size(grid_config),
        "cv_folds": 5,
        "grid_config": grid_config
    }
    
    with open(path, "w") as f:
        json.dump(projection_data, f, indent=2)
    
    logger.info(f"Runtime projection saved to {path}: {runtime_hours:.4f} hours")

def main():
    """Entry point for runtime estimator."""
    # Setup logging to file and console
    setup_logging()
    
    try:
        df = load_aligned_dataset()
        logger.info(f"Dataset loaded: {len(df)} samples, {len(df.columns)} features")
        
        # Define the grid search space as per T026/T047
        grid_config = {
            "max_depth": [3, 5, 7],
            "learning_rate": [0.01, 0.1, 0.2],
            "n_estimators": [50, 100, 200]
        }
        
        runtime = estimate_total_runtime(df, grid_config)
        save_runtime_projection(runtime)
        
        logger.info(f"Projected runtime: {runtime:.2f} hours")
        print(f"Projected runtime: {runtime:.2f} hours")
        
    except FileNotFoundError as e:
        logger.error(f"Critical data missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error estimating runtime: {e}")
        raise

if __name__ == "__main__":
    main()