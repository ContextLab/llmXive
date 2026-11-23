import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve

# Import from sibling modules as per API surface
# Note: The API surface lists load_test_predictions in evaluate.py context,
# but since this is the sensitivity analysis file, we implement the loading here
# or assume the data is passed via arguments. We will implement robust loading.
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution without package structure
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

def load_test_predictions(predictions_path: str) -> pd.DataFrame:
    """
    Load test set predictions from a JSON or CSV file.
    Expected columns: 'isolate_id', 'true_label', 'predicted_prob'
    """
    path = Path(predictions_path)
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    if path.suffix == '.csv':
        df = pd.read_csv(path)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    required_cols = ['true_label', 'predicted_prob']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in predictions: {missing}")
    
    return df

def calculate_metrics_at_threshold(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> Dict[str, float]:
    """
    Calculate False Positive Rate (FPR) and False Negative Rate (FNR) at a specific threshold.
    
    Returns:
        Dictionary with 'threshold', 'fpr', 'fnr', 'tpr' (sensitivity), 'tnr' (specificity)
    """
    y_pred = (y_prob >= threshold).astype(int)
    
    # Confusion matrix: TN, FP, FN, TP
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    # Rates
    # FPR = FP / (FP + TN)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    
    # FNR = FN / (FN + TP)
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    # TPR (Sensitivity) = TP / (TP + FN)
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # TNR (Specificity) = TN / (TN + FP)
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    return {
        'threshold': float(threshold),
        'fpr': float(fpr),
        'fnr': float(fnr),
        'tpr': float(tpr),
        'tnr': float(tnr),
        'tp': int(tp),
        'tn': int(tn),
        'fp': int(fp),
        'fn': int(fn)
    }

def run_sensitivity_sweep(df: pd.DataFrame, threshold_range: Tuple[float, float] = (0.0, 1.0), steps: int = 100) -> List[Dict[str, Any]]:
    """
    Sweep classification thresholds and calculate FPR/FNR variations.
    
    Args:
        df: DataFrame with 'true_label' and 'predicted_prob'
        threshold_range: (min, max) threshold values
        steps: Number of steps in the sweep
    
    Returns:
        List of dictionaries containing metrics for each threshold
    """
    y_true = df['true_label'].values
    y_prob = df['predicted_prob'].values
    
    # Generate thresholds
    thresholds = np.linspace(threshold_range[0], threshold_range[1], steps)
    
    results = []
    for thresh in thresholds:
        metrics = calculate_metrics_at_threshold(y_true, y_prob, thresh)
        results.append(metrics)
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Save sensitivity analysis results to a CSV file.
    
    Args:
        results: List of metric dictionaries
        output_path: Path to save the CSV
    """
    df_results = pd.DataFrame(results)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(output_file, index=False)
    logger.info(f"Sensitivity analysis results saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on model predictions")
    parser.add_argument("--predictions", type=str, required=True, 
                        help="Path to test predictions (CSV or JSON)")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to save sensitivity analysis results (CSV)")
    parser.add_argument("--steps", type=int, default=100,
                        help="Number of threshold steps")
    parser.add_argument("--min-threshold", type=float, default=0.0,
                        help="Minimum threshold value")
    parser.add_argument("--max-threshold", type=float, default=1.0,
                        help="Maximum threshold value")
    
    args = parser.parse_args()
    
    logger.info(f"Loading predictions from {args.predictions}")
    try:
        df = load_test_predictions(args.predictions)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load predictions: {e}")
        sys.exit(1)
    
    logger.info(f"Running sensitivity sweep from {args.min_threshold} to {args.max_threshold} ({args.steps} steps)")
    results = run_sensitivity_sweep(df, (args.min_threshold, args.max_threshold), args.steps)
    
    logger.info(f"Saving results to {args.output}")
    save_results(results, args.output)
    
    # Print summary
    logger.info("Sensitivity Analysis Summary:")
    logger.info(f"  Total isolates: {len(df)}")
    logger.info(f"  Threshold range: [{args.min_threshold}, {args.max_threshold}]")
    logger.info(f"  Steps: {args.steps}")
    
    # Find optimal threshold (minimizing FPR + FNR)
    best_idx = np.argmin([r['fpr'] + r['fnr'] for r in results])
    best = results[best_idx]
    logger.info(f"  Optimal threshold (min FPR+FNR): {best['threshold']:.3f}")
    logger.info(f"    FPR: {best['fpr']:.3f}, FNR: {best['fnr']:.3f}")

if __name__ == "__main__":
    main()