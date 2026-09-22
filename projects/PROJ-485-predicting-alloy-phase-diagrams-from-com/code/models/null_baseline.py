import os
import sys
import argparse
import pickle
import json
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode
from features.export_descriptors import load_processed_data

logger = get_logger(__name__)

def compute_global_mean(train_data: List[Dict[str, Any]]) -> float:
    """
    Compute the mean experimental temperature from the training fold.
    
    Args:
        train_data: List of rows from the training fold.
        
    Returns:
        The mean temperature value (float).
    """
    if not train_data:
        raise ValueError("Training data is empty; cannot compute mean.")
    
    temperatures = [row['temperature'] for row in train_data if 'temperature' in row]
    if not temperatures:
        raise ValueError("No temperature values found in training data.")
        
    return sum(temperatures) / len(temperatures)

def predict_null_model(mean_temp: float, test_data: List[Dict[str, Any]]) -> List[float]:
    """
    Generate predictions for the test fold using the training-fold mean.
    
    Args:
        mean_temp: The global mean temperature from the training set.
        test_data: List of rows from the test fold.
        
    Returns:
        List of predictions (all equal to mean_temp).
    """
    return [mean_temp] * len(test_data)

def evaluate_model(predictions: List[float], actuals: List[float]) -> Dict[str, float]:
    """
    Calculate MAE and R² for the null model predictions.
    
    Args:
        predictions: List of predicted temperatures.
        actuals: List of actual experimental temperatures.
        
    Returns:
        Dictionary with 'mae' and 'r2' metrics.
    """
    if len(predictions) != len(actuals):
        raise ValueError("Predictions and actuals must have the same length.")
    
    n = len(predictions)
    if n == 0:
        return {'mae': 0.0, 'r2': 0.0}
    
    # Calculate MAE
    mae = sum(abs(p - a) for p, a in zip(predictions, actuals)) / n
    
    # Calculate R²
    mean_actual = sum(actuals) / n
    ss_tot = sum((a - mean_actual) ** 2 for a in actuals)
    ss_res = sum((a - p) ** 2 for a, p in zip(actuals, predictions))
    
    if ss_tot == 0:
        r2 = 1.0 if ss_res == 0 else 0.0
    else:
        r2 = 1 - (ss_res / ss_tot)
        
    return {'mae': mae, 'r2': r2}

def compare_models(null_metrics: Dict[str, float], rf_metrics: Dict[str, float]) -> Dict[str, float]:
    """
    Compare null model and Random Forest model performance.
    
    Args:
        null_metrics: Metrics from the null model (MAE, R²).
        rf_metrics: Metrics from the RF model (MAE, R²).
        
    Returns:
        Dictionary with comparison results including percentage improvement.
    """
    null_mae = null_metrics['mae']
    rf_mae = rf_metrics['mae']
    
    if null_mae == 0:
        percentage_improvement = 0.0
    else:
        percentage_improvement = ((null_mae - rf_mae) / null_mae) * 100
        
    return {
        'null_model_mae': null_mae,
        'rf_model_mae': rf_mae,
        'percentage_improvement': percentage_improvement
    }

def run_null_baseline_analysis(loso_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the null model baseline analysis across all LOSO folds.
    
    Args:
        loso_results: Dictionary containing LOSO cross-validation results.
            Expected structure:
            {
                'folds': [
                    {
                        'fold_id': str,
                        'train_data': List[Dict],
                        'test_data': List[Dict],
                        'rf_predictions': List[float],
                        'actuals': List[float],
                        'rf_metrics': Dict[str, float]
                    },
                    ...
                ]
            }
            
    Returns:
        Aggregated comparison results across all folds.
    """
    folds = loso_results.get('folds', [])
    
    if not folds:
        log_warning("No folds found in LOSO results; skipping null baseline analysis.")
        return {'null_model_mae': 0.0, 'rf_model_mae': 0.0, 'percentage_improvement': 0.0}
    
    all_null_predictions = []
    all_actuals = []
    all_rf_predictions = []
    
    for fold in folds:
        train_data = fold.get('train_data', [])
        test_data = fold.get('test_data', [])
        rf_predictions = fold.get('rf_predictions', [])
        actuals = fold.get('actuals', [])
        
        if not train_data or not test_data:
            log_warning(f"Skipping fold {fold.get('fold_id', 'unknown')} due to missing data.")
            continue
        
        # Compute global mean from training data
        mean_temp = compute_global_mean(train_data)
        
        # Generate null model predictions
        null_preds = predict_null_model(mean_temp, test_data)
        
        all_null_predictions.extend(null_preds)
        all_actuals.extend(actuals)
        all_rf_predictions.extend(rf_predictions)
    
    # Evaluate null model
    null_metrics = evaluate_model(all_null_predictions, all_actuals)
    
    # Evaluate RF model (re-aggregate from fold results)
    rf_metrics = evaluate_model(all_rf_predictions, all_actuals)
    
    # Compare models
    comparison = compare_models(null_metrics, rf_metrics)
    
    log_info(f"Null Model MAE: {comparison['null_model_mae']:.2f}")
    log_info(f"RF Model MAE: {comparison['rf_model_mae']:.2f}")
    log_info(f"Percentage Improvement: {comparison['percentage_improvement']:.2f}%")
    
    return comparison

def main():
    """
    Main entry point for running the null baseline analysis.
    """
    parser = argparse.ArgumentParser(description="Run null model baseline analysis")
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/processed/loso_results.pkl',
        help='Path to LOSO results file (pickle)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/artifacts/baseline_comparison.json',
        help='Path to output JSON file'
    )
    
    args = parser.parse_args()
    
    # Load LOSO results
    if not os.path.exists(args.input):
        log_error(f"LOSO results file not found: {args.input}")
        sys.exit(1)
    
    with open(args.input, 'rb') as f:
        loso_results = pickle.load(f)
    
    # Run analysis
    comparison_results = run_null_baseline_analysis(loso_results)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(comparison_results, f, indent=2)
    
    log_info(f"Baseline comparison results saved to {args.output}")
    
    return comparison_results

if __name__ == '__main__':
    main()
