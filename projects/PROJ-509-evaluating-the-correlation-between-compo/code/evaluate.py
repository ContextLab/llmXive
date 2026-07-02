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

# Import project utilities
try:
    from config import load_paths
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution or different import context
    from pathlib import Path
    import sys
    
    # Ensure code directory is in path if running from root
    code_dir = Path(__file__).parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
        
    from config import load_paths
    from utils.logging import get_logger

logger = get_logger(__name__)

def load_data() -> pd.DataFrame:
    """
    Load the computed descriptors dataset.
    
    Returns:
        pd.DataFrame: The dataset with descriptors and formation energy.
    """
    paths = load_paths()
    input_path = paths['processed_descriptors']
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Dataset not found at {input_path}. "
                                "Please run code/descriptors.py first.")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def perform_stratified_split(df: pd.DataFrame, 
                             target_col: str = 'formation_energy', 
                             group_col: str = 'crystal_system',
                             test_size: float = 0.2,
                             random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split of the dataset by crystal system.
    
    Args:
        df: Input dataframe.
        target_col: Column name for the target variable.
        group_col: Column name for stratification.
        test_size: Proportion of data for the test set.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, val_df).
    """
    from sklearn.model_selection import train_test_split
    
    logger.info(f"Performing stratified split by '{group_col}' (test_size={test_size})")
    
    train_df, val_df = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df[group_col], 
        random_state=random_state
    )
    
    logger.info(f"Train set size: {len(train_df)}, Val set size: {len(val_df)}")
    return train_df, val_df

def load_models() -> Dict[str, Any]:
    """
    Load trained models from the evaluation directory.
    
    Returns:
        Dict containing trained models.
    """
    paths = load_paths()
    model_path = paths['trained_models']
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained models not found at {model_path}. "
                                "Please run code/train.py first.")
    
    logger.info(f"Loading models from {model_path}")
    with open(model_path, 'rb') as f:
        models = pickle.load(f)
    
    return models

def calculate_tvd(train_df: pd.DataFrame, 
                  val_df: pd.DataFrame, 
                  group_col: str = 'crystal_system') -> float:
    """
    Calculate Total Variation Distance between training and validation distributions.
    
    Args:
        train_df: Training dataframe.
        val_df: Validation dataframe.
        group_col: Column name for the categorical variable to compare.
        
    Returns:
        float: TVD value between 0 and 1.
    """
    train_dist = train_df[group_col].value_counts(normalize=True).sort_index()
    val_dist = val_df[group_col].value_counts(normalize=True).sort_index()
    
    # Align indices to handle missing categories in one set
    all_categories = train_dist.index.union(val_dist.index)
    train_dist = train_dist.reindex(all_categories, fill_value=0)
    val_dist = val_dist.reindex(all_categories, fill_value=0)
    
    tvd = 0.5 * np.sum(np.abs(train_dist - val_dist))
    return tvd

def evaluate_models(train_df: pd.DataFrame, 
                    val_df: pd.DataFrame, 
                    models: Dict[str, Any],
                    target_col: str = 'formation_energy',
                    feature_cols: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
    """
    Evaluate trained models on training and validation sets.
    
    Args:
        train_df: Training dataframe.
        val_df: Validation dataframe.
        models: Dictionary of trained models.
        target_col: Target variable column name.
        feature_cols: List of feature column names. If None, inferred from model.
        
    Returns:
        Dict of metrics per model.
    """
    if feature_cols is None:
        # Infer feature columns from the dataframe, excluding target and non-feature columns
        exclude_cols = [target_col, 'material_id', 'crystal_system', 'chemical_formula']
        feature_cols = [col for col in train_df.columns if col not in exclude_cols]
    
    logger.info(f"Evaluating models on {len(feature_cols)} features")
    
    X_train = train_df[feature_cols]
    y_train = train_df[target_col]
    X_val = val_df[feature_cols]
    y_val = val_df[target_col]
    
    results = {}
    
    for model_name, model in models.items():
        logger.info(f"Evaluating {model_name}...")
        
        # Predictions
        train_pred = model.predict(X_train)
        val_pred = model.predict(X_val)
        
        # Metrics
        train_r2 = r2_score(y_train, train_pred)
        val_r2 = r2_score(y_val, val_pred)
        train_mae = mean_absolute_error(y_train, train_pred)
        val_mae = mean_absolute_error(y_val, val_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        
        results[model_name] = {
            'train_r2': float(train_r2),
            'val_r2': float(val_r2),
            'train_mae': float(train_mae),
            'val_mae': float(val_mae),
            'train_rmse': float(train_rmse),
            'val_rmse': float(val_rmse)
        }
        
        logger.info(f"{model_name} - Train R²: {train_r2:.4f}, Val R²: {val_r2:.4f}")
    
    return results

def save_metrics(metrics: Dict[str, Dict[str, float]], 
                 tvd: float, 
                 overfitting_ratios: Dict[str, float]) -> None:
    """
    Save evaluation metrics and overfitting ratios to JSON.
    
    Args:
        metrics: Dictionary of model metrics.
        tvd: Total Variation Distance.
        overfitting_ratios: Dictionary of overfitting ratios per model.
    """
    paths = load_paths()
    output_path = paths['model_metrics']
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Prepare final metrics dictionary
    final_metrics = {
        'total_variation_distance': float(tvd),
        'models': metrics,
        'overfitting_analysis': overfitting_ratios
    }
    
    logger.info(f"Saving metrics to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    logger.info("Metrics saved successfully")

def main():
    """Main execution function for model evaluation."""
    print("Starting model evaluation...")
    
    # Load data
    df = load_data()
    
    # Perform stratified split
    train_df, val_df = perform_stratified_split(df)
    
    # Calculate TVD
    tvd = calculate_tvd(train_df, val_df)
    logger.info(f"Total Variation Distance: {tvd:.4f}")
    if tvd > 0.05:
        logger.warning(f"TVD ({tvd:.4f}) exceeds threshold of 0.05. "
                       "Stratification may not be sufficient.")
    
    # Load models
    models = load_models()
    
    # Evaluate models
    metrics = evaluate_models(train_df, val_df, models)
    
    # Calculate overfitting ratios
    overfitting_ratios = {}
    for model_name, model_metrics in metrics.items():
        train_r2 = model_metrics['train_r2']
        val_r2 = model_metrics['val_r2']
        
        # Handle division by zero or near-zero
        if abs(val_r2) < 1e-10:
            if train_r2 > 0:
                ratio = float('inf')
                logger.warning(f"{model_name}: Validation R² near zero, overfitting ratio is infinite.")
            else:
                ratio = 1.0 # If both are zero/negative, assume no overfitting in ratio terms
                logger.warning(f"{model_name}: Both train and val R² near zero.")
        else:
            ratio = train_r2 / val_r2
        
        overfitting_ratios[model_name] = float(ratio)
        logger.info(f"{model_name} Overfitting Ratio (Train R² / Val R²): {ratio:.4f}")
    
    # Save all metrics
    save_metrics(metrics, tvd, overfitting_ratios)
    
    print("Evaluation complete. Results saved to data/evaluation/model_metrics.json")

if __name__ == '__main__':
    main()