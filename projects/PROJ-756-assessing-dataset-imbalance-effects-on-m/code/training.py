import os
import sys
import pickle
import logging
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

# Import memory profiling utilities
from memory_profiler import profile_memory, ensure_results_directory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_data(data_path: str) -> pd.DataFrame:
    """Load processed data from parquet file."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    logger.info(f"Loading data from {data_path}")
    return pd.read_parquet(data_path)

def identify_targets_and_features(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Identify target columns and feature columns."""
    # Assuming target columns start with 'target_' or are specific known names
    # For this pipeline, we assume numeric columns that are not descriptors are targets
    # Or we follow a specific convention. Let's assume columns not in descriptor list are targets.
    # Based on T007/T008a/T008b, descriptors are computed and saved.
    # Let's assume the dataframe has 'composition' and target properties.
    
    # Heuristic: Exclude non-numeric columns and known non-targets
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    targets = [col for col in numeric_cols if col not in ['composition', 'cluster_id']]
    # If specific target names are known, we could filter here. 
    # For now, assume all numeric columns except 'composition' are targets.
    # But typically 'composition' is string.
    
    # Better heuristic: The task description implies we train on descriptors to predict targets.
    # Descriptors are in 'data/processed/descriptors.parquet'.
    # The main data file likely has 'composition', 'target_property', and 'descriptors'.
    
    # Let's assume the input df has columns: 'composition', 'target_<property>', and descriptor columns.
    # We need to separate them.
    # For this implementation, we will assume the user passes a df where the last N columns are targets
    # or we identify them by a prefix.
    
    # Let's assume standard naming: targets are columns starting with 'target_'
    targets = [col for col in df.columns if col.startswith('target_')]
    if not targets:
        # Fallback: assume all numeric columns except 'composition' are targets if no 'target_' prefix
        targets = [col for col in numeric_cols if col != 'composition']
    
    features = [col for col in df.columns if col not in targets and col != 'composition']
    
    return targets, features

def train_models(X: np.ndarray, y: np.ndarray, model_type: str = 'rf') -> Any:
    """Train a model on the given data."""
    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    elif model_type == 'gb':
        model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    model.fit(X, y)
    return model

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """Evaluate a model and return metrics."""
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    return {'MAE': mae, 'RMSE': rmse, 'R2': r2}

@profile_memory(output_path="results/memory_profile.csv")
def run_training_pipeline(data_path: str, output_dir: str, model_types: List[str] = ['rf', 'gb']):
    """
    Main pipeline function to load data, train models, and save results.
    Decorated with memory profiler to log peak usage.
    """
    ensure_results_directory()
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Starting training pipeline...")
    df = load_data(data_path)
    targets, features = identify_targets_and_features(df)
    
    logger.info(f"Found targets: {targets}")
    logger.info(f"Found features: {features}")
    
    if not features:
        logger.error("No features found. Check data schema.")
        return

    # Prepare data
    X = df[features].values
    results = []
    
    for target in targets:
        y = df[target].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        for model_type in model_types:
            logger.info(f"Training {model_type} for target {target}...")
            model = train_models(X_train_scaled, y_train, model_type)
            metrics = evaluate_model(model, X_test_scaled, y_test)
            
            # Save model
            model_path = os.path.join(output_dir, f"{target}_{model_type}.pkl")
            with open(model_path, 'wb') as f:
                pickle.dump({'model': model, 'scaler': scaler}, f)
            
            results.append({
                'property': target,
                'model_type': model_type,
                'MAE': metrics['MAE'],
                'RMSE': metrics['RMSE'],
                'R2': metrics['R2']
            })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_path = os.path.join(output_dir, "training_results.csv")
    results_df.to_csv(results_path, index=False)
    logger.info(f"Training results saved to {results_path}")
    
    return results_df

def main():
    """Entry point for the training module."""
    # Default paths
    data_path = "data/processed/descriptors.parquet" # Or the merged processed data
    output_dir = "results/models"
    
    # Parse arguments if needed
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    run_training_pipeline(data_path, output_dir)

if __name__ == "__main__":
    main()
