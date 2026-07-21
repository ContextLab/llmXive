import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging
from src.models.linear_regressor import run_linear_regression, main as linear_main
from src.models.random_forest_regressor import run_random_forest_regression, main as rf_main
from src.models.training_pipeline import run_training_pipeline, main as training_main
import pandas as pd
import numpy as np

def load_model_metrics(models_dir: Path) -> Dict[str, Any]:
    """
    Load trained models and evaluate them to generate metrics.
    This function assumes models have been trained by T035 (training_pipeline).
    """
    metrics = {}
    
    # Load features data
    features_file = project_root / "data" / "processed" / "alloys_features.csv"
    if not features_file.exists():
        logging.error(f"Features file not found: {features_file}")
        return metrics
        
    df = pd.read_csv(features_file)
    
    # Identify target columns (hysteresis parameters)
    target_cols = ['coercivity_oe', 'saturation_magnetization_emu_g']
    feature_cols = [col for col in df.columns if col not in target_cols + ['composition', 'source_metadata']]
    
    if len(feature_cols) == 0:
        logging.error("No feature columns found in dataset")
        return metrics
        
    X = df[feature_cols].dropna()
    y_coercivity = df.loc[X.index, 'coercivity_oe']
    y_saturation = df.loc[X.index, 'saturation_magnetization_emu_g']
    
    # Check if we have enough data
    if len(X) < 5:
        logging.warning(f"Insufficient data for training: {len(X)} samples")
        return metrics
    
    # Run Linear Regression
    try:
        logging.info("Evaluating Linear Regression model...")
        linear_metrics = run_linear_regression(
            X=X, 
            y_coercivity=y_coercivity, 
            y_saturation=y_saturation,
            feature_names=feature_cols
        )
        metrics['LinearRegression'] = linear_metrics
    except Exception as e:
        logging.error(f"Linear Regression evaluation failed: {e}")
        metrics['LinearRegression'] = {'error': str(e)}
        
    # Run Random Forest
    try:
        logging.info("Evaluating Random Forest model...")
        rf_metrics = run_random_forest_regression(
            X=X, 
            y_coercivity=y_coercivity, 
            y_saturation=y_saturation,
            feature_names=feature_cols
        )
        metrics['RandomForest'] = rf_metrics
    except Exception as e:
        logging.error(f"Random Forest evaluation failed: {e}")
        metrics['RandomForest'] = {'error': str(e)}
        
    return metrics

def aggregate_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate metrics into a standardized format for model_metrics.json.
    """
    aggregated = {
        'generated_at': pd.Timestamp.now().isoformat(),
        'models': {}
    }
    
    for model_name, model_data in metrics.items():
        if 'error' in model_data:
            aggregated['models'][model_name] = {
                'status': 'failed',
                'error': model_data['error']
            }
            continue
            
        aggregated['models'][model_name] = {
            'status': 'success',
            'metrics': {
                'coercivity': {
                    'r2': model_data.get('coercivity_r2', None),
                    'mae': model_data.get('coercivity_mae', None),
                    'rmse': model_data.get('coercivity_rmse', None),
                    'cv_score': model_data.get('coercivity_cv_score', None)
                },
                'saturation_magnetization': {
                    'r2': model_data.get('saturation_r2', None),
                    'mae': model_data.get('saturation_mae', None),
                    'rmse': model_data.get('saturation_rmse', None),
                    'cv_score': model_data.get('saturation_cv_score', None)
                }
            },
            'feature_importance': model_data.get('feature_importance', [])
        }
        
    return aggregated

def main():
    """
    Main entry point for generating model metrics.
    Loads trained models, evaluates them, and writes results to data/processed/model_metrics.json.
    """
    # Setup logging
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = setup_logging(
        log_file=log_dir / "generate_model_metrics.log",
        console_level=logging.INFO
    )
    
    logging.info("Starting model metrics generation...")
    
    # Check if features file exists
    features_file = project_root / "data" / "processed" / "alloys_features.csv"
    if not features_file.exists():
        logging.error(f"Features file not found: {features_file}")
        logging.error("Please run preprocessing and feature engineering pipelines first.")
        sys.exit(1)
    
    # Load and evaluate models
    metrics = load_model_metrics(project_root / "code" / "models")
    
    if not metrics:
        logging.error("No metrics generated. Check for errors above.")
        sys.exit(1)
        
    # Aggregate metrics
    aggregated = aggregate_metrics(metrics)
    
    # Write to output file
    output_file = project_root / "data" / "processed" / "model_metrics.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(aggregated, f, indent=2)
        
    logging.info(f"Model metrics written to {output_file}")
    
    # Print summary
    for model_name, model_data in aggregated['models'].items():
        if model_data['status'] == 'success':
            logging.info(f"{model_name}: Coercivity R²={model_data['metrics']['coercivity']['r2']:.4f}, "
                        f"Saturation R²={model_data['metrics']['saturation_magnetization']['r2']:.4f}")
        else:
            logging.warning(f"{model_name}: Failed - {model_data.get('error', 'Unknown error')}")
            
    logging.info("Model metrics generation complete.")

if __name__ == "__main__":
    main()