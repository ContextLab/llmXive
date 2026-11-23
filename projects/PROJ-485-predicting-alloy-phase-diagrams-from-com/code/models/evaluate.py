import os
import sys
import json
import pickle
import argparse
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Local imports based on provided API surface
from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_loso_results(results_path: str) -> List[Dict[str, Any]]:
    """
    Load LOSO cross-validation results from a JSON file.
    Expected schema: List of dicts with keys:
      - system_id (str)
      - fold_id (str)
      - predictions (List[float])
      - actuals (List[float])
      - errors (List[float])  # pre-calculated or derived here
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"LOSO results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    # Ensure errors are calculated if not present
    for fold_data in data:
        if 'errors' not in fold_data:
            if 'predictions' in fold_data and 'actuals' in fold_data:
                fold_data['errors'] = [p - a for p, a in zip(fold_data['predictions'], fold_data['actuals'])]
            else:
                fold_data['errors'] = []
    
    return data

def calculate_fold_metrics(fold_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate MAE and R² for a single fold."""
    errors = fold_data.get('errors', [])
    actuals = fold_data.get('actuals', [])
    
    if not errors or not actuals:
        return {'mae': 0.0, 'r2': 0.0, 'n_samples': 0}
    
    mae = np.mean([abs(e) for e in errors])
    
    # R² calculation
    ss_res = sum(e**2 for e in errors)
    mean_actual = np.mean(actuals)
    ss_tot = sum((a - mean_actual)**2 for a in actuals)
    
    if ss_tot == 0:
        r2 = 0.0
    else:
        r2 = 1 - (ss_res / ss_tot)
    
    return {
        'mae': float(mae),
        'r2': float(r2),
        'n_samples': len(errors)
    }

def check_data_density(results: List[Dict[str, Any]], logger_obj: logging.Logger) -> Dict[str, Any]:
    """
    Implement T027: Data density check.
    Aggregates errors by system_id, computes standard deviation of errors per system.
    Flags LOW_DATA_DENSITY if:
      - N (count of unique compositions per system_id) < 5
      - OR SD of errors > 50,000 (50K)
    
    Logs to structured log file using T008 Enum (ErrorCode.LOW_DATA_DENSITY).
    """
    system_stats: Dict[str, Dict[str, Any]] = {}
    
    # Aggregate by system_id
    for fold_data in results:
        system_id = fold_data.get('system_id', 'unknown')
        errors = fold_data.get('errors', [])
        
        if system_id not in system_stats:
            system_stats[system_id] = {
                'errors': [],
                'n_samples': 0
            }
        
        system_stats[system_id]['errors'].extend(errors)
        system_stats[system_id]['n_samples'] += len(errors)
    
    flagged_systems = []
    
    for system_id, stats in system_stats.items():
        n_samples = stats['n_samples']
        errors = stats['errors']
        
        # Condition 1: N < 5
        is_low_count = n_samples < 5
        
        # Condition 2: SD > 50K
        sd = np.std(errors) if errors else 0.0
        is_high_sd = sd > 50000.0
        
        if is_low_count or is_high_sd:
            reason = []
            if is_low_count:
                reason.append(f"N={n_samples} < 5")
            if is_high_sd:
                reason.append(f"SD={sd:.2f} > 50000")
            
            log_entry = {
                "system_id": system_id,
                "n_samples": n_samples,
                "std_dev": float(sd),
                "reason": "; ".join(reason),
                "error_code": ErrorCode.LOW_DATA_DENSITY.value
            }
            
            # Log to structured logger
            logger_obj.error(
                json.dumps(log_entry), 
                extra={'error_code': ErrorCode.LOW_DATA_DENSITY}
            )
            
            flagged_systems.append(log_entry)
    
    return {
        'total_systems_analyzed': len(system_stats),
        'flagged_systems': flagged_systems,
        'density_check_passed': len(flagged_systems) == 0
    }

def save_evaluation_report(report: Dict[str, Any], output_path: str) -> None:
    """Save the full evaluation report including density checks to disk."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    log_info(f"Evaluation report saved to {output_path}")

def evaluate_model(
    results_path: str, 
    output_report_path: str,
    density_log_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main evaluation function.
    1. Loads LOSO results.
    2. Calculates per-fold and aggregate metrics (MAE, R²).
    3. Runs data density check (T027).
    4. Saves report.
    """
    log_info(f"Loading LOSO results from {results_path}")
    results = load_loso_results(results_path)
    
    # Calculate fold metrics
    fold_metrics = []
    aggregate_errors = []
    
    for fold in results:
        metrics = calculate_fold_metrics(fold)
        metrics['fold_id'] = fold.get('fold_id', 'unknown')
        metrics['system_id'] = fold.get('system_id', 'unknown')
        fold_metrics.append(metrics)
        
        if 'errors' in fold:
            aggregate_errors.extend(fold['errors'])
    
    # Aggregate metrics
    total_samples = sum(m['n_samples'] for m in fold_metrics)
    overall_mae = np.mean([abs(e) for e in aggregate_errors]) if aggregate_errors else 0.0
    
    ss_res = sum(e**2 for e in aggregate_errors)
    all_actuals = []
    for fold in results:
        all_actuals.extend(fold.get('actuals', []))
    
    mean_actual = np.mean(all_actuals) if all_actuals else 0
    ss_tot = sum((a - mean_actual)**2 for a in all_actuals)
    overall_r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    # T027: Data Density Check
    log_info("Running data density check (T027)...")
    density_result = check_data_density(results, logger)
    
    report = {
        'overall_metrics': {
            'mae': float(overall_mae),
            'r2': float(overall_r2),
            'total_samples': total_samples
        },
        'fold_metrics': fold_metrics,
        'data_density_check': density_result
    }
    
    save_evaluation_report(report, output_report_path)
    
    if density_result['density_check_passed']:
        log_info("Data density check PASSED.")
    else:
        log_warning(
            f"Data density check FAILED for {len(density_result['flagged_systems'])} systems. "
            f"See logs for details. Error Code: {ErrorCode.LOW_DATA_DENSITY.value}"
        )
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Evaluate model performance and check data density.')
    parser.add_argument('--results', type=str, required=True, help='Path to LOSO results JSON file')
    parser.add_argument('--output', type=str, required=True, help='Path to save evaluation report JSON')
    parser.add_argument('--density-log', type=str, default='data/logs/density_check.log', help='Path to density check log file')
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    log_dir = os.path.dirname(args.density_log)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure file handler for density logs if needed, 
    # though the requirement says "Log to structured log file using T008 Enum"
    # The logging module configured in utils/logging.py usually handles the main pipeline log.
    # We will rely on the structured logging from utils.logging which writes to data/logs/pipeline.log
    # as per T004/T008 patterns.
    
    try:
        report = evaluate_model(args.results, args.output)
        print(json.dumps(report, indent=2))
    except Exception as e:
        log_error(f"Evaluation failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()