"""
Module to save trained model artifacts and evaluation metrics.

This module implements Task T026: Saving model artifacts to 
`data/evaluation/trained_models.pkl` and metrics to 
`data/evaluation/model_metrics.json`.
"""
import os
import sys
import json
import pickle
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import local utilities
from config import load_paths
from utils.logging import get_logger
from evaluate import load_models, evaluate_models, calculate_tvd, load_data
from train import train_models, perform_stratified_split

# Setup logger
logger = get_logger(__name__)

def save_artifacts(
    models: Dict[str, Any], 
    metrics: Dict[str, Any],
    output_models_path: Optional[str] = None,
    output_metrics_path: Optional[str] = None
) -> None:
    """
    Save trained models and evaluation metrics to disk.
    
    Args:
        models: Dictionary containing trained model objects keyed by name.
        metrics: Dictionary containing evaluation metrics.
        output_models_path: Path to save the models pickle file.
        output_metrics_path: Path to save the metrics JSON file.
        
    Raises:
        FileNotFoundError: If the output directory does not exist.
        IOError: If writing to the file fails.
    """
    paths = load_paths()
    
    # Determine output paths
    if output_models_path is None:
        output_models_path = str(paths['data_evaluation'] / 'trained_models.pkl')
    if output_metrics_path is None:
        output_metrics_path = str(paths['data_evaluation'] / 'model_metrics.json')
    
    # Ensure directory exists
    models_dir = Path(output_models_path).parent
    metrics_dir = Path(output_metrics_path).parent
    
    models_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    # Save models
    logger.info(f"Saving models to {output_models_path}")
    try:
        with open(output_models_path, 'wb') as f:
            pickle.dump(models, f)
        logger.info("Models saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save models: {e}")
        raise
    
    # Save metrics
    logger.info(f"Saving metrics to {output_metrics_path}")
    try:
        with open(output_metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)
        logger.info("Metrics saved successfully.")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        raise

def main() -> None:
    """
    Main entry point for saving models and metrics.
    
    This function orchestrates the full pipeline to ensure data is processed,
    models are trained, metrics are calculated (including overfitting ratio),
    and finally everything is saved to the designated output files.
    """
    logger.info("Starting model and metrics saving process (T026).")
    paths = load_paths()
    
    # 1. Load Data
    logger.info("Loading processed data...")
    data_path = paths['data_processed'] / 'computed_descriptors.csv'
    if not data_path.exists():
        raise FileNotFoundError(f"Required data file not found: {data_path}")
    
    df, feature_cols, target_col = load_data(data_path)
    logger.info(f"Loaded {len(df)} rows with {len(feature_cols)} features.")
    
    # 2. Split Data
    logger.info("Performing stratified split...")
    X_train, X_val, y_train, y_val, y_train_sys, y_val_sys = perform_stratified_split(
        df, feature_cols, target_col
    )
    
    # 3. Train Models
    logger.info("Training models...")
    models = train_models(X_train, y_train)
    logger.info("Models trained.")
    
    # 4. Calculate Metrics
    logger.info("Calculating evaluation metrics...")
    metrics = evaluate_models(models, X_val, y_val, X_train, y_train, target_col)
    
    # 5. Calculate TVD
    logger.info("Calculating Total Variation Distance...")
    tvd = calculate_tvd(y_train_sys, y_val_sys)
    metrics['tvd'] = tvd
    if tvd > 0.05:
        logger.warning(f"TVD ({tvd:.4f}) exceeds threshold (0.05). Split may be unbalanced.")
    else:
        logger.info(f"TVD ({tvd:.4f}) is within acceptable limits.")
    
    # 6. Calculate Overfitting Ratio (from T025)
    # Ensure we have train and val r2 for both models
    for model_name in ['random_forest', 'gradient_boosting']:
        if model_name in metrics:
            model_metrics = metrics[model_name]
            if 'train_r2' in model_metrics and 'val_r2' in model_metrics:
                val_r2 = model_metrics['val_r2']
                train_r2 = model_metrics['train_r2']
                
                # Handle division by zero or near-zero
                if abs(val_r2) < 1e-9:
                    model_metrics['overfitting_ratio'] = float('inf') if train_r2 > 0 else 0.0
                    logger.warning(f"Val R2 near zero for {model_name}. Overfitting ratio set to infinity.")
                else:
                    model_metrics['overfitting_ratio'] = train_r2 / val_r2
                
                logger.info(f"{model_name} overfitting ratio: {model_metrics['overfitting_ratio']:.4f}")
    
    # 7. Save Artifacts
    logger.info("Saving artifacts...")
    save_artifacts(models, metrics)
    
    logger.info("T026 completed successfully.")

if __name__ == "__main__":
    main()