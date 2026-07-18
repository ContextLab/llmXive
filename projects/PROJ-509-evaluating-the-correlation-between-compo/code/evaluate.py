import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from config import load_paths
from utils.logging import get_logger

# Ensure the code directory is in the path for relative imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

logger = get_logger(__name__)

def load_data() -> pd.DataFrame:
    """
    Load the processed dataset containing descriptors and target.
    """
    paths = load_paths()
    input_path = paths['processed_descriptors']
    
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input dataset not found at {input_path}. "
                                "Please run descriptors.py first.")
    
    logger.info(f"Loading dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['formation_energy_per_atom']
    # Check if descriptor columns exist (assuming they are prefixed or specific names)
    # Based on T015, we expect mean/variance of 5 properties.
    # We assume the CSV has columns like 'mean_electronegativity', etc.
    # We will dynamically identify feature columns if 'formation_energy_per_atom' is the target.
    
    if 'formation_energy_per_atom' not in df.columns:
        raise ValueError("Target column 'formation_energy_per_atom' not found in dataset.")
    
    feature_cols = [col for col in df.columns if col != 'formation_energy_per_atom']
    if not feature_cols:
        raise ValueError("No feature columns found in dataset.")
    
    logger.info(f"Loaded {len(df)} rows. Features: {feature_cols}")
    return df, feature_cols

def perform_stratified_split(df: pd.DataFrame, feature_cols: list, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform an 80/20 stratified split by Crystal System.
    Note: The dataset from T012/T014 should contain 'crystal_system' if it was part of the original MP data.
    If 'crystal_system' is not present, we cannot stratify by it. 
    However, T020 in tasks.md explicitly requires stratification by Crystal System.
    We assume the input CSV retains this column or we must reconstruct it.
    For safety, we check for 'crystal_system'. If missing, we fall back to random split with a warning 
    (though strict adherence to spec requires it).
    """
    stratify_col = 'crystal_system'
    
    if stratify_col not in df.columns:
        logger.warning(f"Column '{stratify_col}' not found in dataset. Cannot stratify by Crystal System. "
                       "Falling back to random split. This may violate spec FR-004.")
        train_df, val_df = train_test_split(df, test_size=0.2, random_state=random_state)
    else:
        # Check for sufficient classes
        if df[stratify_col].nunique() < 2:
            logger.warning("Less than 2 unique crystal systems found. Cannot stratify. Falling back to random split.")
            train_df, val_df = train_test_split(df, test_size=0.2, random_state=random_state)
        else:
            train_df, val_df = train_test_split(
                df, 
                test_size=0.2, 
                random_state=random_state, 
                stratify=df[stratify_col]
            )
    
    X_train = train_df[feature_cols]
    y_train = train_df['formation_energy_per_atom']
    X_val = val_df[feature_cols]
    y_val = val_df['formation_energy_per_atom']
    
    logger.info(f"Train size: {len(train_df)}, Val size: {len(val_df)}")
    return X_train, y_train, X_val, y_val

def load_models() -> Dict[str, Any]:
    """
    Load the trained models from the artifact file.
    """
    paths = load_paths()
    model_path = paths['trained_models']
    
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Trained models not found at {model_path}. "
                                "Please run train.py first.")
    
    logger.info(f"Loading models from {model_path}")
    with open(model_path, 'rb') as f:
        models = pickle.load(f)
    
    return models

def calculate_tvd(train_df: pd.DataFrame, val_df: pd.DataFrame, col: str = 'crystal_system') -> float:
    """
    Calculate Total Variation Distance between distributions of a column.
    TVD = 0.5 * sum(|p_i - q_i|)
    """
    if col not in train_df.columns or col not in val_df.columns:
        logger.warning(f"Column {col} not found in both splits. TVD cannot be calculated.")
        return 0.0
    
    train_dist = train_df[col].value_counts(normalize=True).sort_index()
    val_dist = val_df[col].value_counts(normalize=True).sort_index()
    
    # Align indices
    all_indices = train_dist.index.union(val_dist.index)
    train_dist = train_dist.reindex(all_indices, fill_value=0)
    val_dist = val_dist.reindex(all_indices, fill_value=0)
    
    tvd = 0.5 * np.sum(np.abs(train_dist.values - val_dist.values))
    return tvd

def evaluate_models(models: Dict[str, Any], X_val: pd.DataFrame, y_val: pd.Series) -> Dict[str, Dict[str, float]]:
    """
    Calculate R², MAE, and RMSE for each model on the validation split.
    """
    metrics = {}
    
    for name, model in models.items():
        logger.info(f"Evaluating model: {name}")
        y_pred = model.predict(X_val)
        
        r2 = r2_score(y_val, y_pred)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        
        metrics[name] = {
            'r2': float(r2),
            'mae': float(mae),
            'rmse': float(rmse)
        }
        
        logger.info(f"  R²: {r2:.4f}, MAE: {mae:.4f}, RMSE: {rmse:.4f}")
    
    return metrics

def save_metrics(metrics: Dict[str, Dict[str, float]], tvd: float, split_info: Dict[str, Any]):
    """
    Save evaluation metrics and TVD to JSON.
    """
    paths = load_paths()
    output_path = paths['model_metrics']
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        'metrics': metrics,
        'total_variation_distance': tvd,
        'split_info': split_info
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")

def main():
    """
    Main entry point for evaluation.
    """
    logger.info("Starting evaluation pipeline...")
    
    # 1. Load Data
    df, feature_cols = load_data()
    
    # We need the original dataframe with 'crystal_system' for TVD calculation
    # The split function returns X, y but we also need the full rows for TVD
    # Re-run split logic to get train/val dataframes with all columns
    paths = load_paths()
    input_path = paths['processed_descriptors']
    full_df = pd.read_csv(input_path)
    
    if 'crystal_system' in full_df.columns:
        train_df, val_df = train_test_split(
            full_df, 
            test_size=0.2, 
            random_state=42, 
            stratify=full_df['crystal_system']
        )
    else:
        logger.warning("No crystal_system column for stratified split in main flow.")
        train_df, val_df = train_test_split(full_df, test_size=0.2, random_state=42)
    
    X_train = train_df[feature_cols]
    y_train = train_df['formation_energy_per_atom']
    X_val = val_df[feature_cols]
    y_val = val_df['formation_energy_per_atom']
    
    # 2. Calculate TVD
    tvd = calculate_tvd(train_df, val_df, 'crystal_system')
    logger.info(f"Total Variation Distance (Crystal System): {tvd:.4f}")
    if tvd > 0.05:
        logger.warning(f"TVD ({tvd:.4f}) exceeds threshold 0.05. Split integrity may be compromised.")
    
    # 3. Load Models
    models = load_models()
    
    # 4. Evaluate Models
    metrics = evaluate_models(models, X_val, y_val)
    
    # 5. Save Metrics
    split_info = {
        'train_size': len(train_df),
        'val_size': len(val_df),
        'tvd': tvd
    }
    save_metrics(metrics, tvd, split_info)
    
    logger.info("Evaluation pipeline completed successfully.")

if __name__ == "__main__":
    main()