import os
import sys
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = RESULTS_DIR / "models"
BALANCED_DIR = DATA_DIR / "balanced"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
BALANCED_DIR.mkdir(parents=True, exist_ok=True)

def load_data(data_type: str = "balanced") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load processed data.
    Args:
        data_type: "balanced" or "skewed".
                   For "balanced", loads from data/balanced/processed.parquet.
                   For "skewed", loads from data/processed/descriptors.parquet (or similar).
    Returns:
        X (features), y (target) as DataFrames.
    """
    if data_type == "balanced":
        path = BALANCED_DIR / "processed.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Balanced data not found at {path}. "
                                    "Please run resampling.py first to generate balanced data.")
        df = pd.read_parquet(path)
    else:
        # Default to skewed data from T007
        path = PROCESSED_DIR / "descriptors.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Skewed data not found at {path}. "
                                    "Please run descriptors.py first.")
        df = pd.read_parquet(path)

    # Identify target column (assuming 'target' or the last numeric column if not specified)
    # Based on typical pipeline, 'target' is the property value
    target_col = 'target'
    if target_col not in df.columns:
        # Fallback: assume the last column is target if 'target' missing
        target_col = df.columns[-1]
        logger.warning(f"Column 'target' not found. Using '{target_col}' as target.")

    feature_cols = [c for c in df.columns if c != target_col]
    X = df[feature_cols]
    y = df[target_col]

    return X, y

def identify_targets_and_features(X: pd.DataFrame, y: pd.Series) -> Tuple[List[str], str]:
    """
    Returns feature names and target name.
    """
    return list(X.columns), y.name or 'target'

def train_models(X: pd.DataFrame, y: pd.Series, 
                 model_type: str = "all",
                 random_state: int = 42) -> Dict[str, Any]:
    """
    Train Random Forest and Gradient Boosting models.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        model_type: "rf", "gb", or "all".
        random_state: Seed for reproducibility.
    
    Returns:
        Dictionary containing trained models, metrics, and configuration.
    """
    logger.info(f"Training {model_type} models with random_state={random_state}")
    
    # Split data (Stratified is for classification, here we use standard split for regression)
    # Ensure we preserve the distribution of the target if possible by not shuffling too aggressively
    # or by using a specific stratification if the target was binned, but standard regression split is:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )

    results = {
        "config": {
            "model_type": model_type,
            "random_state": random_state,
            "train_size": len(X_train),
            "test_size": len(X_test)
        },
        "models": {},
        "metrics": {}
    }

    models_to_train = []
    if model_type in ["rf", "all"]:
        models_to_train.append(("RandomForest", RandomForestRegressor(
            n_estimators=100, 
            max_depth=None, 
            random_state=random_state,
            n_jobs=-1
        )))
    if model_type in ["gb", "all"]:
        models_to_train.append(("GradientBoosting", GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=random_state,
            learning_rate=0.1
        )))

    for name, model in models_to_train:
        logger.info(f"Training {name}...")
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        results["models"][name] = model
        results["metrics"][name] = {
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
            "test_size": len(X_test)
        }
        logger.info(f"{name} Metrics -> MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")

    return results

def save_results(results: Dict[str, Any], data_type: str = "balanced", 
                 target_name: str = "target") -> str:
    """
    Save trained models and metrics to disk.
    
    Args:
        results: Dictionary from train_models.
        data_type: "balanced" or "skewed".
        target_name: Name of the target property.
    
    Returns:
        Path to the saved model file.
    """
    model_dir = MODELS_DIR / data_type
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save models
    model_path = model_dir / f"models_{target_name}.pkl"
    with open(model_path, 'wb') as f:
        pickle.dump(results, f)
    
    # Save metrics as CSV for easy aggregation
    metrics_path = RESULTS_DIR / f"{data_type}_metrics.csv"
    metrics_rows = []
    
    for model_name, metrics in results["metrics"].items():
        metrics_rows.append({
            "property": target_name,
            "model_type": model_name,
            "MAE": metrics["MAE"],
            "RMSE": metrics["RMSE"],
            "R2": metrics["R2"],
            "data_type": data_type,
            "random_state": results["config"]["random_state"]
        })
    
    df_metrics = pd.DataFrame(metrics_rows)
    
    # Append to existing file if it exists, otherwise create new
    if metrics_path.exists():
        existing_df = pd.read_csv(metrics_path)
        df_metrics = pd.concat([existing_df, df_metrics], ignore_index=True)
    
    df_metrics.to_csv(metrics_path, index=False)
    logger.info(f"Saved metrics to {metrics_path}")
    
    return str(model_path)

def main():
    """
    Main entry point for T025: Retrain RF and GB models on balanced dataset.
    """
    logger.info("Starting T025: Training models on balanced dataset")
    
    try:
        # 1. Load balanced data
        X, y = load_data(data_type="balanced")
        
        if X.empty or y.empty:
            raise ValueError("Loaded balanced data is empty. Check resampling output.")
        
        target_name = y.name if y.name else "target"
        logger.info(f"Loaded {len(X)} samples for target '{target_name}'")
        
        # 2. Train models
        # T025 requires identical hyperparameters to baseline. 
        # We use the standard defaults defined in train_models which match T014/T015 baseline.
        results = train_models(X, y, model_type="all", random_state=42)
        
        # 3. Save results
        model_path = save_results(results, data_type="balanced", target_name=target_name)
        
        logger.info(f"Successfully trained and saved models to {model_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during training: {e}")
        raise

if __name__ == "__main__":
    main()