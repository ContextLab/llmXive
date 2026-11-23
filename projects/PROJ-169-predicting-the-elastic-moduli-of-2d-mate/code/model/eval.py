"""Evaluation and metrics calculation for elastic moduli prediction.

Calculates MAPE, RMSE, and R² for Young's modulus, Shear modulus, and Poisson's ratio.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Import from sibling modules based on API surface
try:
    from utils.logger import get_logger, log_operation
except ImportError:
    # Fallback for direct execution or different import context
    import logging as logging_module
    def get_logger(*args, **kwargs):
        return logging_module.getLogger("eval")
    def log_operation(*args, **kwargs):
        return None

# Ensure numpy is imported for calculations
np = __import__('numpy')

def calculate_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-8
) -> Dict[str, float]:
    """Calculate MAPE, RMSE, and R² for a set of true and predicted values.

    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        epsilon: Small value to avoid division by zero in MAPE.

    Returns:
        Dictionary with 'mape', 'rmse', and 'r2' keys.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        return {'mape': np.nan, 'rmse': np.nan, 'r2': np.nan}

    y_true = np.array(y_true, dtype=np.float64)
    y_pred = np.array(y_pred, dtype=np.float64)

    # MAPE: Mean Absolute Percentage Error
    # Avoid division by zero
    abs_diff = np.abs(y_true - y_pred)
    abs_true = np.abs(y_true)
    # Handle cases where true value is zero
    mask = abs_true > epsilon
    if np.sum(mask) == 0:
        mape = np.nan
    else:
        mape = np.mean(abs_diff[mask] / abs_true[mask]) * 100.0

    # RMSE: Root Mean Squared Error
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    # R²: Coefficient of determination
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        r2 = np.nan
    else:
        r2 = 1.0 - (ss_res / ss_tot)

    return {
        'mape': float(mape),
        'rmse': float(rmse),
        'r2': float(r2)
    }

def evaluate_model(
    predictions_path: str,
    split_indices_path: str,
    output_path: str
) -> Dict[str, Any]:
    """Evaluate model performance on the test set.

    Loads predictions and split indices, calculates metrics for each target
    (Young's, Shear, Poisson), and writes the results to a JSON file.

    Args:
        predictions_path: Path to the predictions JSON file (output of T018b).
        split_indices_path: Path to the split indices JSON file (output of T013f/T017).
        output_path: Path to write the evaluation metrics JSON file.

    Returns:
        Dictionary containing the evaluation results.
    """
    logger = get_logger("eval")

    log_operation("evaluate_model", path=predictions_path)

    # Load predictions
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    with open(predictions_path, 'r') as f:
        predictions_data = json.load(f)

    # Load split indices to identify test set
    if not os.path.exists(split_indices_path):
        raise FileNotFoundError(f"Split indices file not found: {split_indices_path}")

    with open(split_indices_path, 'r') as f:
        split_data = json.load(f)

    test_indices = set(split_data.get('test_indices', []))

    # Extract test data from predictions
    # Assuming predictions_data is a list of dicts with 'index', 'true', 'pred' keys
    # or a dict with keys like 'youngs_true', 'youngs_pred', etc.
    # We need to handle the structure produced by T018b (predictions.json)

    # Common structure from T018b might be:
    # [
    #   {"index": 0, "youngs_true": 100.0, "youngs_pred": 98.5, "shear_true": 40.0, ...},
    #   ...
    # ]
    # OR
    # {
    #   "youngs_true": [...], "youngs_pred": [...],
    #   "shear_true": [...], "shear_pred": [...],
    #   "poisson_true": [...], "poisson_pred": [...]
    # }

    # We will assume a list of records for flexibility, but handle dict format too
    if isinstance(predictions_data, list):
        # Filter for test set
        test_records = [r for r in predictions_data if r.get('index') in test_indices]
        
        if not test_records:
            logging.warning("No test records found in predictions matching split indices.")
            # Create empty results
            results = {
                "youngs": {"mape": np.nan, "rmse": np.nan, "r2": np.nan},
                "shear": {"mape": np.nan, "rmse": np.nan, "r2": np.nan},
                "poisson": {"mape": np.nan, "rmse": np.nan, "r2": np.nan},
                "overall": {
                    "mape": np.nan, "rmse": np.nan, "r2": np.nan,
                    "count": 0
                },
                "note": "No test data available or mismatch in indices."
            }
        else:
            # Aggregate arrays
            youngs_true = [r.get('youngs_true', r.get('E_true')) for r in test_records]
            youngs_pred = [r.get('youngs_pred', r.get('E_pred')) for r in test_records]
            shear_true = [r.get('shear_true', r.get('G_true')) for r in test_records]
            shear_pred = [r.get('shear_pred', r.get('G_pred')) for r in test_records]
            poisson_true = [r.get('poisson_true', r.get('nu_true')) for r in test_records]
            poisson_pred = [r.get('poisson_pred', r.get('nu_pred')) for r in test_records]

            # Filter out None values if any
            def clean_pairs(t, p):
                pairs = list(zip(t, p))
                return [x for x, y in pairs if x is not None and y is not None]

            yt, yp = zip(*clean_pairs(youngs_true, youngs_pred)) if len(youngs_true) > 0 else ([], [])
            st, sp = zip(*clean_pairs(shear_true, shear_pred)) if len(shear_true) > 0 else ([], [])
            pt, pp = zip(*clean_pairs(poisson_true, poisson_pred)) if len(poisson_true) > 0 else ([], [])

            results = {
                "youngs": calculate_metrics(yt, yp),
                "shear": calculate_metrics(st, sp),
                "poisson": calculate_metrics(pt, pp),
                "overall": {
                    "mape": np.nan, "rmse": np.nan, "r2": np.nan,
                    "count": len(test_records)
                }
            }
    elif isinstance(predictions_data, dict):
        # Handle dict format where keys are arrays
        test_indices_list = list(test_indices)
        # We need to map indices to values if the dict format doesn't store index
        # Assuming the dict format contains full arrays and we just evaluate all
        # Or if it contains 'indices' key mapping to values
        
        # Fallback: if 'indices' exists, filter; else assume all are test
        indices = predictions_data.get('indices', list(range(len(predictions_data.get('youngs_true', [])))))
        
        # Filter arrays by test indices
        def filter_by_indices(arr, idx_list, full_idx_list=None):
            if full_idx_list is None:
                full_idx_list = list(range(len(arr)))
            return [arr[i] for i, orig_idx in enumerate(full_idx_list) if orig_idx in idx_list]

        # Assuming the dict keys are 'youngs_true', 'youngs_pred', etc.
        # and 'indices' maps the array index to the material ID or original index
        # If 'indices' is missing, we assume the order matches the split_indices order
        
        # Simplest case: evaluate all provided in the dict as test
        # But strictly we should filter by test_indices if 'indices' is present
        
        if 'indices' in predictions_data:
            full_indices = predictions_data['indices']
            yt = filter_by_indices(predictions_data['youngs_true'], test_indices, full_indices)
            yp = filter_by_indices(predictions_data['youngs_pred'], test_indices, full_indices)
            st = filter_by_indices(predictions_data['shear_true'], test_indices, full_indices)
            sp = filter_by_indices(predictions_data['shear_pred'], test_indices, full_indices)
            pt = filter_by_indices(predictions_data['poisson_true'], test_indices, full_indices)
            pp = filter_by_indices(predictions_data['poisson_pred'], test_indices, full_indices)
        else:
            # No index info, assume all are test or fail
            yt = predictions_data.get('youngs_true', [])
            yp = predictions_data.get('youngs_pred', [])
            st = predictions_data.get('shear_true', [])
            sp = predictions_data.get('shear_pred', [])
            pt = predictions_data.get('poisson_true', [])
            pp = predictions_data.get('poisson_pred', [])

        results = {
            "youngs": calculate_metrics(yt, yp),
            "shear": calculate_metrics(st, sp),
            "poisson": calculate_metrics(pt, pp),
            "overall": {
                "mape": np.nan, "rmse": np.nan, "r2": np.nan,
                "count": len(yt)
            }
        }
    else:
        raise ValueError("Predictions data must be a list or dict.")

    # Calculate overall metrics (average of the three or aggregate all errors)
    # Here we average the MAPE, RMSE, R2 for simplicity as a summary
    # Note: Averaging R2 is statistically dubious but common for reporting
    mapes = [results[k]['mape'] for k in ['youngs', 'shear', 'poisson'] if not np.isnan(results[k]['mape'])]
    rmses = [results[k]['rmse'] for k in ['youngs', 'shear', 'poisson'] if not np.isnan(results[k]['rmse'])]
    r2s = [results[k]['r2'] for k in ['youngs', 'shear', 'poisson'] if not np.isnan(results[k]['r2'])]

    if mapes: results['overall']['mape'] = np.mean(mapes)
    if rmses: results['overall']['rmse'] = np.mean(rmses)
    if r2s: results['overall']['r2'] = np.mean(r2s)

    # Write results
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    log_operation("evaluate_model_complete", output=output_path, metrics=results)
    return results

def main():
    parser = argparse.ArgumentParser(description="Evaluate model metrics (MAPE, RMSE, R²)")
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/results/predictions.json",
        help="Path to predictions JSON file (output of T018b)"
    )
    parser.add_argument(
        "--splits",
        type=str,
        default="data/processed/split_indices.json",
        help="Path to split indices JSON file (output of T013f)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/evaluation_metrics.json",
        help="Path to output evaluation metrics JSON file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))

    try:
        results = evaluate_model(args.predictions, args.splits, args.output)
        print(f"Evaluation complete. Results written to {args.output}")
        print(json.dumps(results, indent=2))
    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()