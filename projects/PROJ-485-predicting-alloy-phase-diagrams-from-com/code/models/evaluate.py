import os
import sys
import json
import pickle
import argparse
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

def load_loso_results(results_path: str) -> List[Dict[str, Any]]:
    """
    Load LOSO cross-validation results from a JSON file.
    Expected structure: list of fold results, each containing predictions, targets, and metadata.
    """
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"LOSO results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    return data

def calculate_fold_metrics(fold_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate MAE and R² for a single fold.
    """
    predictions = np.array(fold_data.get('predictions', []))
    targets = np.array(fold_data.get('targets', []))
    
    if len(predictions) == 0 or len(targets) == 0:
        return {'mae': 0.0, 'r2': 0.0, 'count': 0}
    
    mae = np.mean(np.abs(predictions - targets))
    
    ss_res = np.sum((targets - predictions) ** 2)
    ss_tot = np.sum((targets - np.mean(targets)) ** 2)
    
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    
    return {
        'mae': float(mae),
        'r2': float(r2),
        'count': len(predictions)
    }

def save_evaluation_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the evaluation report to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    log_info(f"Evaluation report saved to {output_path}")

def evaluate_model(
    results_path: str,
    output_path: str,
    processed_data_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate the model using LOSO results.
    
    Performs:
    1. Calculates aggregate metrics (MAE, R²) across folds.
    2. Implements data density check (T027):
       - Aggregates errors by system_id.
       - Computes standard deviation of errors per system.
       - Flags LOW_DATA_DENSITY if N < 5 OR SD > 50K (50,000).
    
    Args:
        results_path: Path to the LOSO results JSON file.
        output_path: Path to save the evaluation report.
        processed_data_path: Path to the processed data CSV (for system_id mapping).
    
    Returns:
        Dict containing evaluation metrics and density check results.
    """
    log_info(f"Loading LOSO results from {results_path}")
    loso_results = load_loso_results(results_path)
    
    if not isinstance(loso_results, list) or len(loso_results) == 0:
        raise ValueError("LOSO results must be a non-empty list of fold results.")
    
    fold_metrics = []
    all_errors = []
    
    # Collect errors and metadata for density check
    for i, fold in enumerate(loso_results):
        metrics = calculate_fold_metrics(fold)
        fold_metrics.append(metrics)
        log_info(f"Fold {i}: MAE={metrics['mae']:.4f}, R²={metrics['r2']:.4f}, Count={metrics['count']}")
        
        # Extract errors for density check if system_id is available
        if 'system_ids' in fold and 'errors' in fold:
            system_ids = fold['system_ids']
            errors = fold['errors']
            for sid, err in zip(system_ids, errors):
                all_errors.append({'system_id': sid, 'error': err})
        elif 'predictions' in fold and 'targets' in fold:
            # Fallback: calculate errors if not pre-computed
            preds = np.array(fold['predictions'])
            tgts = np.array(fold['targets'])
            errors = preds - tgts
            # If system_ids are not provided, we can't aggregate by system
            # We'll skip density check for this fold if no system_ids
            pass
    
    # Aggregate fold metrics
    avg_mae = np.mean([m['mae'] for m in fold_metrics])
    avg_r2 = np.mean([m['r2'] for m in fold_metrics])
    total_count = sum(m['count'] for m in fold_metrics)
    
    report = {
        'aggregate_metrics': {
            'mean_mae': float(avg_mae),
            'mean_r2': float(avg_r2),
            'total_samples': total_count
        },
        'fold_metrics': fold_metrics,
        'data_density_check': {
            'performed': len(all_errors) > 0,
            'systems_flagged': [],
            'details': []
        }
    }
    
    # T027: Data Density Check
    if len(all_errors) > 0:
        log_info("Performing data density check (T027)...")
        
        # Group errors by system_id
        system_errors: Dict[str, List[float]] = {}
        for item in all_errors:
            sid = item['system_id']
            err = item['error']
            if sid not in system_errors:
                system_errors[sid] = []
            system_errors[sid].append(err)
        
        flagged_systems = []
        details = []
        
        for sid, errors in system_errors.items():
            n = len(errors)
            sd = np.std(errors) if n > 1 else 0.0
            
            # Flag if N < 5 OR SD > 50,000 (50K)
            is_flagged = False
            reasons = []
            
            if n < 5:
                is_flagged = True
                reasons.append(f"N={n} < 5")
            
            if sd > 50000:
                is_flagged = True
                reasons.append(f"SD={sd:.2f} > 50000")
            
            detail = {
                'system_id': sid,
                'n_samples': n,
                'std_dev': float(sd),
                'flagged': is_flagged
            }
            if is_flagged:
                detail['reasons'] = reasons
                flagged_systems.append(sid)
            
            details.append(detail)
            
            if is_flagged:
                log_warning(
                    f"LOW_DATA_DENSITY flag raised for system '{sid}': "
                    f"N={n}, SD={sd:.2f}. Reasons: {', '.join(reasons)}"
                )
                # Log error code as per spec
                logger.warning(f"Error Code: {ErrorCode.LOW_DATA_DENSITY.value} for system {sid}")
        
        report['data_density_check'] = {
            'performed': True,
            'systems_flagged': flagged_systems,
            'total_systems_analyzed': len(system_errors),
            'details': details
        }
        
        if flagged_systems:
            log_warning(f"Data density check flagged {len(flagged_systems)} systems: {flagged_systems}")
    else:
        log_warning("Data density check skipped: No system-level errors available.")
    
    save_evaluation_report(report, output_path)
    return report

def main() -> None:
    """
    Main entry point for the evaluation script.
    """
    parser = argparse.ArgumentParser(description="Evaluate model performance and check data density.")
    parser.add_argument(
        "--results",
        type=str,
        default="data/artifacts/loso_results.json",
        help="Path to LOSO results JSON file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/artifacts/evaluation_report.json",
        help="Path to save evaluation report."
    )
    parser.add_argument(
        "--processed-data",
        type=str,
        default="data/processed/descriptors.csv",
        help="Path to processed data CSV (optional, for system_id mapping)."
    )
    
    args = parser.parse_args()
    
    try:
        report = evaluate_model(
            results_path=args.results,
            output_path=args.output,
            processed_data_path=args.processed_data
        )
        log_info("Evaluation completed successfully.")
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        log_error(f"Invalid data: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error during evaluation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()