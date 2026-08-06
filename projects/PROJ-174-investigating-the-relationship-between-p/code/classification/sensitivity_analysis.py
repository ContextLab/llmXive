import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Add parent directory to path to allow imports from project root
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_config
from logging_config import get_logger

# Thresholds defined in SC-004
THRESHOLDS = [0.40, 0.50, 0.60]

def load_classification_predictions(predictions_path: str) -> pd.DataFrame:
    """
    Load classification predictions from the output of the classification pipeline.
    Expected columns: subject_id, trial_id, predicted_probability, true_label, search_time
    """
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Classification predictions not found at {predictions_path}")
    
    df = pd.read_csv(predictions_path)
    
    # Validate required columns
    required_cols = ['predicted_probability', 'true_label']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in predictions: {missing}")
    
    return df

def compute_metrics_at_threshold(
    df: pd.DataFrame, 
    threshold: float
) -> Dict[str, float]:
    """
    Compute classification metrics at a specific probability threshold.
    
    Metrics:
      - accuracy
      - precision
      - recall
      - f1_score
      - specificity
    """
    # Binarize predictions
    y_pred = (df['predicted_probability'] >= threshold).astype(int)
    y_true = df['true_label'].astype(int)
    
    # Calculate metrics
    tp = ((y_pred == 1) & (y_true == 1)).sum()
    tn = ((y_pred == 0) & (y_true == 0)).sum()
    fp = ((y_pred == 1) & (y_true == 0)).sum()
    fn = ((y_pred == 0) & (y_true == 1)).sum()
    
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    return {
        'threshold': threshold,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'specificity': specificity,
        'tp': int(tp),
        'tn': int(tn),
        'fp': int(fp),
        'fn': int(fn)
    }

def calculate_stability_metrics(
    metrics_list: List[Dict[str, float]]
) -> List[Dict[str, float]]:
    """
    Calculate relative decrease or stability metrics between consecutive thresholds.
    Uses the first threshold (0.40) as the baseline.
    """
    if len(metrics_list) < 2:
        return metrics_list
    
    baseline = metrics_list[0]
    baseline_threshold = baseline['threshold']
    
    results = []
    
    # First row is baseline
    first_row = metrics_list[0].copy()
    first_row['relative_decrease_accuracy'] = 0.0
    first_row['relative_decrease_precision'] = 0.0
    first_row['relative_decrease_recall'] = 0.0
    first_row['relative_decrease_f1'] = 0.0
    first_row['stability_status'] = 'BASELINE'
    results.append(first_row)
    
    for i in range(1, len(metrics_list)):
        current = metrics_list[i].copy()
        current_threshold = current['threshold']
        
        # Calculate relative decrease: (baseline - current) / baseline
        def safe_rel_decrease(baseline_val, current_val):
            if baseline_val == 0:
                return 0.0 if current_val == 0 else float('inf')
            return (baseline_val - current_val) / baseline_val
        
        rel_dec_acc = safe_rel_decrease(baseline['accuracy'], current['accuracy'])
        rel_dec_prec = safe_rel_decrease(baseline['precision'], current['precision'])
        rel_dec_rec = safe_rel_decrease(baseline['recall'], current['recall'])
        rel_dec_f1 = safe_rel_decrease(baseline['f1_score'], current['f1_score'])
        
        # Determine stability status
        # If relative decrease is small (< 5%), mark as STABLE
        # If decrease is moderate (5-20%), mark as MODERATE_DECREASE
        # If decrease is large (> 20%), mark as LARGE_DECREASE
        avg_decrease = np.mean([rel_dec_acc, rel_dec_prec, rel_dec_rec, rel_dec_f1])
        
        if avg_decrease <= 0.05:
            status = 'STABLE'
        elif avg_decrease <= 0.20:
            status = 'MODERATE_DECREASE'
        else:
            status = 'LARGE_DECREASE'
        
        current['relative_decrease_accuracy'] = rel_dec_acc
        current['relative_decrease_precision'] = rel_dec_prec
        current['relative_decrease_recall'] = rel_dec_rec
        current['relative_decrease_f1'] = rel_dec_f1
        current['stability_status'] = status
        
        results.append(current)
    
    return results

def run_sensitivity_analysis(
    predictions_path: str,
    output_path: str,
    thresholds: List[float] = None
) -> pd.DataFrame:
    """
    Run full sensitivity analysis across specified thresholds.
    
    Args:
        predictions_path: Path to classification predictions CSV
        output_path: Path to write sensitivity analysis results
        thresholds: List of thresholds to evaluate (defaults to SC-004 values)
    
    Returns:
        DataFrame with sensitivity analysis results
    """
    if thresholds is None:
        thresholds = THRESHOLDS
    
    logger = get_logger(__name__)
    logger.info(f"Loading predictions from {predictions_path}")
    df = load_classification_predictions(predictions_path)
    
    logger.info(f"Computing metrics for thresholds: {thresholds}")
    metrics_list = []
    for t in thresholds:
        metrics = compute_metrics_at_threshold(df, t)
        metrics_list.append(metrics)
        logger.debug(f"Threshold {t}: Accuracy={metrics['accuracy']:.4f}, "
                    f"F1={metrics['f1_score']:.4f}")
    
    # Calculate stability metrics
    logger.info("Calculating stability metrics")
    enriched_metrics = calculate_stability_metrics(metrics_list)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(enriched_metrics)
    
    # Add caveat note if ground truth is derived from median split
    # This is a common scenario in this project (see T029)
    caveat = "Ground truth derived from search-time median split; predictive validity claims removed. See results/limitations.md."
    results_df['caveat'] = caveat
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis results saved to {output_path}")
    
    return results_df

def main():
    """Main entry point for sensitivity analysis script."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis on classification predictions"
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="data/processed/classification_predictions.csv",
        help="Path to classification predictions CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/sensitivity_analysis.csv",
        help="Path to output sensitivity analysis CSV"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Load config for logging setup if needed
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Warning: Could not load config: {e}. Using defaults.")
        config = {}
    
    # Setup logging
    logger = get_logger(__name__)
    logger.info("Starting sensitivity analysis")
    
    try:
        results = run_sensitivity_analysis(
            predictions_path=args.predictions,
            output_path=args.output
        )
        
        # Print summary
        print("\nSensitivity Analysis Summary:")
        print("-" * 80)
        for _, row in results.iterrows():
            print(f"Threshold {row['threshold']:.2f}: "
                  f"Acc={row['accuracy']:.3f}, "
                  f"F1={row['f1_score']:.3f}, "
                  f"Status={row['stability_status']}")
        
        logger.info("Sensitivity analysis completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()