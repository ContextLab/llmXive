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
from config import load_paths, load_env
from utils.logging import get_logger

# Ensure the project root is in the path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logger = get_logger(__name__)

def load_data() -> pd.DataFrame:
    """
    Load the processed dataset with computed descriptors.
    Returns:
        pd.DataFrame: The dataset containing features and target.
    """
    paths = load_paths()
    input_path = paths["data_processed"] / "computed_descriptors.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure target column exists
    if "formation_energy_per_atom" not in df.columns:
        raise ValueError("Target column 'formation_energy_per_atom' not found in dataset.")
    
    return df

def perform_stratified_split(
    df: pd.DataFrame, 
    test_size: float = 0.2, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split by Crystal System.
    Args:
        df: Input dataframe.
        test_size: Fraction of data for testing.
        random_state: Random seed for reproducibility.
    Returns:
        Tuple of (train_df, val_df).
    """
    if "crystal_system" not in df.columns:
        raise ValueError("Column 'crystal_system' not found for stratification.")
    
    train_df, val_df = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df["crystal_system"], 
        random_state=random_state
    )
    
    logger.info(f"Split complete: Train {len(train_df)}, Val {len(val_df)}")
    return train_df, val_df

def load_models(models_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load trained models from disk.
    Args:
        models_path: Path to the pickle file. Defaults to config path.
    Returns:
        Dict containing trained model objects.
    """
    if models_path is None:
        paths = load_paths()
        models_path = paths["data_evaluation"] / "trained_models.pkl"
    
    if not models_path.exists():
        raise FileNotFoundError(f"Models file not found: {models_path}")
    
    logger.info(f"Loading models from {models_path}")
    with open(models_path, "rb") as f:
        models = pickle.load(f)
    
    return models

def calculate_tvd(train_df: pd.DataFrame, val_df: pd.DataFrame, column: str = "crystal_system") -> float:
    """
    Calculate Total Variation Distance between distributions in train and val sets.
    Args:
        train_df: Training dataframe.
        val_df: Validation dataframe.
        column: Column to compare distributions.
    Returns:
        float: TVD value.
    """
    train_dist = train_df[column].value_counts(normalize=True).sort_index()
    val_dist = val_df[column].value_counts(normalize=True).sort_index()
    
    # Align indices to ensure comparison is valid
    all_indices = train_dist.index.union(val_dist.index)
    train_dist = train_dist.reindex(all_indices, fill_value=0)
    val_dist = val_dist.reindex(all_indices, fill_value=0)
    
    tvd = 0.5 * np.sum(np.abs(train_dist.values - val_dist.values))
    logger.info(f"TVD for {column}: {tvd:.4f}")
    return tvd

def evaluate_models(
    models: Dict[str, Any], 
    train_df: pd.DataFrame, 
    val_df: pd.DataFrame, 
    target_col: str = "formation_energy_per_atom", 
    feature_cols: Optional[list] = None
) -> Dict[str, Dict[str, float]]:
    """
    Evaluate models on train and validation sets, calculate overfitting ratio.
    Args:
        models: Dict of model name -> model object.
        train_df: Training dataframe.
        val_df: Validation dataframe.
        target_col: Name of target column.
        feature_cols: List of feature columns. If None, inferred.
    Returns:
        Dict of metrics per model including overfitting_ratio.
    """
    if feature_cols is None:
        # Infer feature columns: all numeric except target
        feature_cols = [c for c in train_df.columns if c != target_col and train_df[c].dtype in ['float64', 'int64']]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_val = val_df[feature_cols]
    y_val = val_df[target_col]
    
    metrics = {}
    
    for name, model in models.items():
        logger.info(f"Evaluating {name}...")
        
        # Predictions
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        # Metrics
        train_r2 = r2_score(y_train, train_pred)
        val_r2 = r2_score(y_val, val_pred)
        val_mae = mean_absolute_error(y_val, val_pred)
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        
        # Overfitting Ratio Calculation
        # Handle division by zero: if val_r2 is 0, ratio is infinite (or cap it)
        if val_r2 == 0:
            overfitting_ratio = float('inf') if train_r2 > 0 else 1.0
        else:
            overfitting_ratio = train_r2 / val_r2
        
        metrics[name] = {
            "train_r2": float(train_r2),
            "val_r2": float(val_r2),
            "val_mae": float(val_mae),
            "val_rmse": float(val_rmse),
            "overfitting_ratio": float(overfitting_ratio)
        }
        
        logger.info(f"{name} - Train R2: {train_r2:.4f}, Val R2: {val_r2:.4f}, Overfitting Ratio: {overfitting_ratio:.4f}")
    
    return metrics

def save_metrics(metrics: Dict[str, Dict[str, float]], output_path: Optional[Path] = None) -> None:
    """
    Save metrics to JSON file.
    Args:
        metrics: Metrics dictionary.
        output_path: Output path. Defaults to config path.
    """
    if output_path is None:
        paths = load_paths()
        output_path = paths["data_evaluation"] / "model_metrics.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")

def main():
    """
    Main entry point for evaluation script.
    1. Load data
    2. Split data (stratified)
    3. Load models
    4. Evaluate models (including overfitting ratio)
    5. Calculate TVD
    6. Save metrics
    """
    load_env()
    logger.info("Starting evaluation pipeline...")
    
    # 1. Load Data
    df = load_data()
    
    # 2. Split Data
    train_df, val_df = perform_stratified_split(df)
    
    # 3. Load Models
    models = load_models()
    
    # 4. Evaluate Models
    metrics = evaluate_models(models, train_df, val_df)
    
    # 5. Calculate TVD
    tvd = calculate_tvd(train_df, val_df)
    
    # Append TVD to metrics for completeness
    metrics["_split_validation"] = {"tvd": tvd}
    
    # 6. Save Metrics
    save_metrics(metrics)
    
    logger.info("Evaluation pipeline completed successfully.")

if __name__ == "__main__":
    main()