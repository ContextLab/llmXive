"""
Script to save consolidated metrics summary to results/metrics.json.

This script aggregates model performance metrics (R², MAE, RMSE),
statistical test results (paired t-test p-values with Bonferroni correction),
and significance flags into a single JSON report.

It depends on:
- data/processed/test.csv: Test dataset with ground truth values
- Pickled model predictions from code/02_statistical_evaluation.py
- Pickled statistical test results from code/02_statistical_evaluation.py
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import setup_logging, get_config

# Setup logging
logger = setup_logging("02_save_metrics")
config = get_config()

def load_test_data() -> Dict[str, np.ndarray]:
    """Load ground truth data from test.csv"""
    import pandas as pd
    test_path = project_root / "data" / "processed" / "test.csv"
    
    if not test_path.exists():
        raise FileNotFoundError(f"Test data not found at {test_path}")
    
    df = pd.read_csv(test_path)
    
    if 'packing_coefficient' not in df.columns:
        raise ValueError("Test data missing 'packing_coefficient' column")
    
    return {
        'ids': df['id'].values if 'id' in df.columns else np.arange(len(df)),
        'y_true': df['packing_coefficient'].values
    }

def load_model_predictions() -> Dict[str, np.ndarray]:
    """Load model predictions from pickled files"""
    predictions = {}
    models = ['random_forest', 'gradient_boosting', 'mean_baseline']
    
    for model_name in models:
        pred_path = project_root / "state" / "projects" / "PROJ-238-predicting-molecular-crystal-packing-fro" / f"{model_name}_predictions.pkl"
        
        if not pred_path.exists():
            logger.warning(f"Predictions file not found for {model_name}: {pred_path}")
            continue
        
        with open(pred_path, 'rb') as f:
            predictions[model_name] = pickle.load(f)
    
    if not predictions:
        raise FileNotFoundError("No model prediction files found")
    
    return predictions

def load_statistical_results() -> Dict[str, Any]:
    """Load statistical test results from pickled file"""
    stats_path = project_root / "state" / "projects" / "PROJ-238-predicting-molecular-crystal-packing-fro" / "statistical_tests.pkl"
    
    if not stats_path.exists():
        raise FileNotFoundError(f"Statistical results not found at {stats_path}")
    
    with open(stats_path, 'rb') as f:
        return pickle.load(f)

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculate R², MAE, and RMSE"""
    return {
        'r2': float(r2_score(y_true, y_pred)),
        'mae': float(mean_absolute_error(y_true, y_pred)),
        'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred)))
    }

def main():
    """Main function to generate and save consolidated metrics"""
    logger.info("Starting metrics consolidation...")
    
    # Load data
    try:
        test_data = load_test_data()
        predictions = load_model_predictions()
        stats_results = load_statistical_results()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load required data: {e}")
        sys.exit(1)
    
    # Ensure we have predictions for all models
    required_models = ['random_forest', 'gradient_boosting', 'mean_baseline']
    missing_models = [m for m in required_models if m not in predictions]
    
    if missing_models:
        logger.error(f"Missing predictions for models: {missing_models}")
        sys.exit(1)
    
    # Calculate metrics for each model
    metrics_summary = {
        'models': {},
        'statistical_tests': {},
        'metadata': {
            'dataset_size': len(test_data['y_true']),
            'generated_at': None,  # Will be set by config
            'project_id': 'PROJ-238-predicting-molecular-crystal-packing-fro'
        }
    }
    
    for model_name in required_models:
        y_pred = predictions[model_name]
        
        # Validate lengths match
        if len(y_pred) != len(test_data['y_true']):
            logger.error(f"Length mismatch for {model_name}: predictions={len(y_pred)}, ground_truth={len(test_data['y_true'])}")
            sys.exit(1)
        
        model_metrics = calculate_metrics(test_data['y_true'], y_pred)
        metrics_summary['models'][model_name] = model_metrics
    
    # Add statistical test results
    metrics_summary['statistical_tests'] = {
        'paired_t_tests': stats_results.get('paired_t_tests', {}),
        'bonferroni_corrected': stats_results.get('bonferroni_corrected', {}),
        'alpha_corrected': stats_results.get('alpha_corrected', 0.025),
        'significance_flags': stats_results.get('significance_flags', {})
    }
    
    # Add metadata
    metrics_summary['metadata']['generated_at'] = config.get('TIMESTAMP', 'unknown')
    
    # Ensure results directory exists
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metrics to JSON
    output_path = results_dir / "metrics.json"
    with open(output_path, 'w') as f:
        json.dump(metrics_summary, f, indent=2)
    
    logger.info(f"Metrics saved to {output_path}")
    logger.info(f"Models included: {list(metrics_summary['models'].keys())}")
    logger.info(f"Statistical tests included: {list(metrics_summary['statistical_tests'].keys())}")
    
    # Print summary
    print("\n=== Metrics Summary ===")
    for model_name, model_metrics in metrics_summary['models'].items():
        print(f"{model_name}:")
        print(f"  R²: {model_metrics['r2']:.4f}")
        print(f"  MAE: {model_metrics['mae']:.4f}")
        print(f"  RMSE: {model_metrics['rmse']:.4f}")
    
    print(f"\nStatistical significance (Bonferroni α={metrics_summary['statistical_tests']['alpha_corrected']}):")
    for model, is_significant in metrics_summary['statistical_tests']['significance_flags'].items():
        status = "✓ Significant" if is_significant else "✗ Not significant"
        print(f"  {model}: {status}")

if __name__ == "__main__":
    main()