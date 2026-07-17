"""
Script to generate model_metrics.json with R² and MAE for Linear and Random Forest models.

This script loads the trained models and their metrics from the training pipeline
and aggregates them into a single JSON file for reporting and validation.

Dependencies:
- src.models.training_pipeline (for loading metrics)
- src.utils.logging_config (for logging setup)
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging_config import setup_logging
from src.models.training_pipeline import main as training_main
from src.models.linear_regressor import save_metrics as linear_save_metrics, run_linear_regression
from src.models.random_forest_regressor import save_metrics as rf_save_metrics, run_random_forest_regression
from src.models.feature_engineering_pipeline import main as feature_engineering_main

# Note: We assume the training pipeline has already been run (T035)
# and models/metrics are saved in code/models/

def load_model_metrics(models_dir: Path) -> Dict[str, Any]:
    """
    Load metrics for both Linear and Random Forest models.
    
    Args:
        models_dir: Path to the directory containing saved model metrics.
        
    Returns:
        Dictionary containing metrics for both models.
    """
    metrics = {}
    
    # Load Linear Regression metrics
    linear_metrics_path = models_dir / "linear_regression_metrics.json"
    if linear_metrics_path.exists():
        with open(linear_metrics_path, 'r') as f:
            metrics['linear_regression'] = json.load(f)
    else:
        logging.warning(f"Linear regression metrics not found at {linear_metrics_path}")
        metrics['linear_regression'] = {'error': 'Metrics file not found'}
    
    # Load Random Forest metrics
    rf_metrics_path = models_dir / "random_forest_metrics.json"
    if rf_metrics_path.exists():
        with open(rf_metrics_path, 'r') as f:
            metrics['random_forest'] = json.load(f)
    else:
        logging.warning(f"Random Forest metrics not found at {rf_metrics_path}")
        metrics['random_forest'] = {'error': 'Metrics file not found'}
    
    return metrics

def aggregate_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate metrics into a standardized format for the final report.
    
    Args:
        metrics: Raw metrics dictionary from load_model_metrics.
        
    Returns:
        Standardized metrics dictionary.
    """
    aggregated = {
        'models': {},
        'summary': {
            'best_model': None,
            'best_r2': -float('inf'),
            'best_mae': float('inf')
        },
        'metadata': {
            'generated_by': 'generate_model_metrics.py',
            'task_id': 'T037'
        }
    }
    
    for model_name, model_metrics in metrics.items():
        if 'error' in model_metrics:
            aggregated['models'][model_name] = model_metrics
            continue
        
        # Ensure we have the expected fields
        r2 = model_metrics.get('r2', None)
        mae = model_metrics.get('mae', None)
        
        aggregated['models'][model_name] = {
            'r2': r2,
            'mae': mae,
            'details': model_metrics
        }
        
        # Update best model tracking
        if r2 is not None and r2 > aggregated['summary']['best_r2']:
            aggregated['summary']['best_r2'] = r2
            aggregated['summary']['best_model'] = model_name
        if mae is not None and mae < aggregated['summary']['best_mae']:
            aggregated['summary']['best_mae'] = mae
    
    return aggregated

def main():
    """Main entry point for the script."""
    logger = setup_logging("generate_model_metrics", log_level=logging.INFO)
    
    # Define paths
    models_dir = project_root / "code" / "models"
    output_dir = project_root / "data" / "processed"
    output_file = output_dir / "model_metrics.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading model metrics from {models_dir}")
    
    # Load metrics
    raw_metrics = load_model_metrics(models_dir)
    
    # Aggregate metrics
    aggregated_metrics = aggregate_metrics(raw_metrics)
    
    # Save to JSON
    with open(output_file, 'w') as f:
        json.dump(aggregated_metrics, f, indent=2)
    
    logger.info(f"Model metrics saved to {output_file}")
    logger.info(f"Best model: {aggregated_metrics['summary']['best_model']} "
               f"(R²={aggregated_metrics['summary']['best_r2']:.4f}, "
               f"MAE={aggregated_metrics['summary']['best_mae']:.4f})")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())