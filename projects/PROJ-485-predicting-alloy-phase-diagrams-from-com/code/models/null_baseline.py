import os
import sys
import argparse
import pickle
import json
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_processed_data(filepath: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Load processed descriptor data from CSV.
    Returns: (rows, column_names)
    """
    if not os.path.exists(filepath):
        log_error(f"Processed data file not found: {filepath}", ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    rows = []
    column_names = []
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        column_names = reader.fieldnames or []
        for row in reader:
            # Convert numeric columns
            processed_row = {}
            for key, value in row.items():
                if key in ['temperature', 'composition', 'mean_atomic_radius', 
                           'electronegativity_variance', 'valence_electron_count', 
                           'hume_rothery_concentration']:
                    try:
                        processed_row[key] = float(value)
                    except (ValueError, TypeError):
                        processed_row[key] = value
                else:
                    processed_row[key] = value
            rows.append(processed_row)
    
    return rows, column_names

def compute_global_mean(data: List[Dict[str, Any]], target_column: str = 'temperature') -> float:
    """
    Compute the global mean of the target column from the dataset.
    This serves as the null model prediction.
    """
    values = []
    for row in data:
        if target_column in row and isinstance(row[target_column], (int, float)):
            values.append(row[target_column])
    
    if not values:
        log_error("No valid values found for global mean calculation", ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError("No valid values found for global mean calculation")
    
    return sum(values) / len(values)

def predict_null_model(data: List[Dict[str, Any]], global_mean: float) -> List[float]:
    """
    Predict using the null model (global mean) for all samples.
    """
    return [global_mean] * len(data)

def evaluate_model(y_true: List[float], y_pred: List[float]) -> Dict[str, float]:
    """
    Calculate MAE and R² for the model predictions.
    """
    if len(y_true) != len(y_pred):
        log_error("y_true and y_pred must have the same length", ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError("y_true and y_pred must have the same length")
    
    if len(y_true) == 0:
        log_error("Empty dataset for evaluation", ErrorCode.INVALID_DATA_SCHEMA)
        raise ValueError("Empty dataset for evaluation")
    
    # Calculate MAE
    mae = sum(abs(t - p) for t, p in zip(y_true, y_pred)) / len(y_true)
    
    # Calculate R²
    mean_true = sum(y_true) / len(y_true)
    ss_tot = sum((t - mean_true) ** 2 for t in y_true)
    ss_res = sum((t - p) ** 2 for t, p in zip(y_true, y_pred))
    
    if ss_tot == 0:
        r_squared = 1.0 if ss_res == 0 else 0.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
    
    return {
        'mae': mae,
        'r_squared': r_squared
    }

def compare_models(null_metrics: Dict[str, float], rf_metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Compare null model and RF model metrics.
    Returns a dictionary with the comparison results.
    """
    null_mae = null_metrics['mae']
    rf_mae = rf_metrics['mae']
    
    if null_mae == 0:
        percentage_improvement = 100.0 if rf_mae == 0 else 0.0
    else:
        percentage_improvement = ((null_mae - rf_mae) / null_mae) * 100.0
    
    return {
        'null_model_mae': null_mae,
        'rf_model_mae': rf_mae,
        'percentage_improvement': percentage_improvement
    }

def run_null_baseline_analysis(
    processed_data_path: str,
    loso_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main function to run the null baseline analysis.
    
    1. Load processed data.
    2. Compute global mean (null model).
    3. Evaluate null model on the same data.
    4. Load RF model results (LOSO cross-validation).
    5. Compare null model MAE vs RF model MAE.
    6. Save comparison to JSON.
    """
    log_info(f"Loading processed data from {processed_data_path}")
    data, _ = load_processed_data(processed_data_path)
    
    # Extract true values (temperature)
    y_true = [row['temperature'] for row in data if 'temperature' in row]
    
    log_info("Computing global mean for null model")
    global_mean = compute_global_mean(data, target_column='temperature')
    
    log_info("Generating null model predictions")
    y_pred_null = predict_null_model(data, global_mean)
    
    log_info("Evaluating null model")
    null_metrics = evaluate_model(y_true, y_pred_null)
    log_info(f"Null Model MAE: {null_metrics['mae']:.4f}, R²: {null_metrics['r_squared']:.4f}")
    
    # Load RF model results
    log_info(f"Loading LOSO results from {loso_results_path}")
    if not os.path.exists(loso_results_path):
        log_error(f"LOSO results file not found: {loso_results_path}", ErrorCode.DATA_SOURCE_MISSING)
        raise FileNotFoundError(f"LOSO results file not found: {loso_results_path}")
    
    with open(loso_results_path, 'r', encoding='utf-8') as f:
        loso_results = json.load(f)
    
    # Extract RF MAE from LOSO results (aggregate)
    if 'aggregate' in loso_results and 'mae' in loso_results['aggregate']:
        rf_mae = loso_results['aggregate']['mae']
    elif 'mae' in loso_results:
        rf_mae = loso_results['mae']
    else:
        # Fallback: calculate from fold results if available
        if 'fold_results' in loso_results:
            fold_maes = [fold.get('mae', 0) for fold in loso_results['fold_results'] if 'mae' in fold]
            if fold_maes:
                rf_mae = sum(fold_maes) / len(fold_maes)
            else:
                log_error("Could not extract RF MAE from LOSO results", ErrorCode.INVALID_DATA_SCHEMA)
                raise ValueError("Could not extract RF MAE from LOSO results")
        else:
            log_error("LOSO results structure not recognized", ErrorCode.INVALID_DATA_SCHEMA)
            raise ValueError("LOSO results structure not recognized")
    
    rf_metrics = {'mae': rf_mae}
    
    log_info("Comparing models")
    comparison = compare_models(null_metrics, rf_metrics)
    
    log_info(f"Comparison - Null MAE: {comparison['null_model_mae']:.4f}, "
             f"RF MAE: {comparison['rf_model_mae']:.4f}, "
             f"Improvement: {comparison['percentage_improvement']:.2f}%")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save comparison to JSON
    log_info(f"Saving comparison results to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2)
    
    log_info("Null baseline analysis completed successfully")
    return comparison

def main():
    """
    CLI entry point for null baseline analysis.
    """
    parser = argparse.ArgumentParser(description='Run null model baseline analysis')
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv',
                      help='Path to processed descriptor data CSV')
    parser.add_argument('--loso-results', type=str, default='data/artifacts/loso_results.json',
                      help='Path to LOSO cross-validation results JSON')
    parser.add_argument('--output', type=str, default='data/artifacts/baseline_comparison.json',
                      help='Path to output comparison JSON')
    
    args = parser.parse_args()
    
    try:
        result = run_null_baseline_analysis(
            processed_data_path=args.data,
            loso_results_path=args.loso_results,
            output_path=args.output
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        log_error(f"Null baseline analysis failed: {str(e)}", ErrorCode.INSUFFICIENT_POWER)
        sys.exit(1)

if __name__ == '__main__':
    main()
