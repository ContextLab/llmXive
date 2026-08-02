"""
Sensitivity Analysis for Classification Thresholds.

Implements SC-004: Sweep thresholds {0.40, 0.50, 0.60} and report metrics
including relative decrease/stability.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np

# Import from local project modules as per API surface
from config import load_config
from classification.evaluate import load_held_out_data, compute_metrics
from classification.ground_truth import load_search_time_data, label_by_median_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants from SC-004
THRESHOLDS_TO_SWEEP = [0.40, 0.50, 0.60]
DEFAULT_BASELINE_THRESHOLD = 0.50

def load_classification_predictions(predictions_path: Path) -> pd.DataFrame:
    """
    Load predicted probabilities from the classification pipeline.
    Expects a CSV with columns including 'predicted_probability' and 'subject_id', 'trial_id'.
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    df = pd.read_csv(predictions_path)
    required_cols = ['predicted_probability']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Predictions file missing required columns: {missing}")
    
    logger.info(f"Loaded predictions with shape {df.shape} from {predictions_path}")
    return df

def compute_metrics_at_threshold(
    df: pd.DataFrame, 
    true_labels: pd.Series, 
    threshold: float
) -> Dict[str, float]:
    """
    Compute classification metrics (Accuracy, Precision, Recall, F1, ROC-AUC)
    for a specific decision threshold.
    
    Args:
        df: DataFrame with 'predicted_probability' column.
        true_labels: Series of binary ground truth labels (0 or 1).
        threshold: Probability cutoff for classifying as positive.
        
    Returns:
        Dictionary of metric names to values.
    """
    preds = (df['predicted_probability'] >= threshold).astype(int)
    
    # Basic counts
    tp = ((preds == 1) & (true_labels == 1)).sum()
    tn = ((preds == 0) & (true_labels == 0)).sum()
    fp = ((preds == 1) & (true_labels == 0)).sum()
    fn = ((preds == 0) & (true_labels == 1)).sum()
    
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    # ROC-AUC calculation (manual implementation for simplicity without sklearn dependency if needed, 
    # but using sklearn if available is standard. Assuming sklearn is available from requirements.txt)
    try:
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(true_labels, df['predicted_probability'])
    except ImportError:
        # Fallback manual calculation if sklearn missing (unlikely given requirements)
        # Sort by probability
        sorted_indices = df['predicted_probability'].argsort()
        sorted_true = true_labels.iloc[sorted_indices]
        sorted_prob = df['predicted_probability'].iloc[sorted_indices]
        
        n_pos = sorted_true.sum()
        n_neg = len(sorted_true) - n_pos
        
        if n_pos == 0 or n_neg == 0:
            auc = 0.5
        else:
            # Mann-Whitney U statistic approach
            sum_rank_pos = 0
            current_rank = 1
            for i, val in enumerate(sorted_prob):
                if sorted_true.iloc[i] == 1:
                    sum_rank_pos += current_rank
                current_rank += 1
            
            auc = (sum_rank_pos - (n_pos * (n_pos + 1) / 2)) / (n_pos * n_neg)

    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'roc_auc': auc,
        'true_positives': int(tp),
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn)
    }

def run_sensitivity_analysis(
    predictions_df: pd.DataFrame,
    true_labels: pd.Series,
    thresholds: List[float] = THRESHOLDS_TO_SWEEP
) -> pd.DataFrame:
    """
    Run sensitivity analysis across specified thresholds.
    
    Returns a DataFrame with metrics for each threshold and relative changes.
    """
    results = []
    baseline_metrics = None
    
    for thresh in thresholds:
        metrics = compute_metrics_at_threshold(predictions_df, true_labels, thresh)
        metrics['threshold'] = thresh
        results.append(metrics)
        
        if abs(thresh - DEFAULT_BASELINE_THRESHOLD) < 1e-6:
            baseline_metrics = metrics
    
    df_results = pd.DataFrame(results)
    
    # Calculate relative changes against baseline (if baseline exists in the sweep)
    if baseline_metrics is not None:
        for metric in ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']:
            baseline_val = baseline_metrics[metric]
            if baseline_val != 0:
                # Relative decrease (negative means improvement if metric is error, but here metrics are higher=better)
                # We calculate (baseline - current) / baseline. 
                # Positive value = decrease in performance. Negative value = improvement.
                # Or "Stability" = 1 - |change|/baseline? 
                # Requirement: "relative decrease or stability metrics"
                # Let's define 'relative_decrease' as (Baseline - Current) / Baseline.
                # If Current < Baseline, this is positive (decrease).
                # If Current > Baseline, this is negative (improvement).
                col_name = f'{metric}_relative_decrease'
                df_results[col_name] = (baseline_val - df_results[metric]) / baseline_val
            else:
                df_results[f'{metric}_relative_decrease'] = np.nan
    else:
        logger.warning(f"Baseline threshold {DEFAULT_BASELINE_THRESHOLD} not found in sweep {thresholds}. Skipping relative decrease calculation.")
        
    return df_results

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on classification thresholds.")
    parser.add_argument(
        '--predictions', 
        type=str, 
        default='results/classification_predictions.csv',
        help='Path to CSV with predicted probabilities.'
    )
    parser.add_argument(
        '--ground-truth',
        type=str,
        default='data/processed/labeled_search_time.csv',
        help='Path to CSV with ground truth labels.'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/sensitivity_analysis.csv',
        help='Path to output CSV file.'
    )
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading predictions from {args.predictions}")
    try:
        predictions_df = load_classification_predictions(Path(args.predictions))
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"Loading ground truth from {args.ground-truth}")
    try:
        # Assuming the labeled data has a 'label' or 'ground_truth' column
        # We use the ground_truth module to ensure consistent loading logic if needed,
        # but here we just load the CSV directly as the labeling is already done.
        gt_df = pd.read_csv(args.ground_truth)
        
        # Identify label column
        label_col = None
        for col in ['label', 'ground_truth', 'is_high_load']:
            if col in gt_df.columns:
                label_col = col
                break
        
        if not label_col:
            raise ValueError(f"Could not find label column in {args.ground_truth}. Expected one of ['label', 'ground_truth', 'is_high_load']")
        
        # Merge predictions and labels on common keys (subject_id, trial_id)
        common_keys = [k for k in ['subject_id', 'trial_id'] if k in predictions_df.columns and k in gt_df.columns]
        if not common_keys:
            raise ValueError("No common keys (subject_id, trial_id) found between predictions and ground truth.")
        
        merged_df = pd.merge(predictions_df, gt_df[common_keys + [label_col]], on=common_keys, how='inner')
        
        if merged_df.empty:
            raise ValueError("Merge between predictions and ground truth resulted in empty DataFrame.")
        
        true_labels = merged_df[label_col]
        predictions_df_merged = merged_df.drop(columns=[label_col]) # Keep only prediction cols for metric calc
        
    except FileNotFoundError as e:
        logger.error(f"Ground truth file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error processing ground truth: {e}")
        sys.exit(1)

    logger.info(f"Running sensitivity analysis on thresholds: {THRESHOLDS_TO_SWEEP}")
    results_df = run_sensitivity_analysis(predictions_df_merged, true_labels, THRESHOLDS_TO_SWEEP)

    # Add caveat note if ground truth was derived from median split
    # We check if the ground truth file path suggests it or if we can detect it.
    # For now, we add a standard caveat if the file name contains 'median' or similar.
    caveat = ""
    if 'median' in args.ground_truth.lower():
        caveat = "Ground truth derived from search-time median split; predictive validity claims removed. Metrics reflect stability relative to baseline (0.50)."
        results_df['caveat'] = caveat
    
    # Ensure output columns are in a logical order
    cols_order = ['threshold', 'accuracy', 'precision', 'recall', 'f1_score', 'roc_auc', 
                  'true_positives', 'true_negatives', 'false_positives', 'false_negatives']
    # Add relative decrease columns if they exist
    rel_cols = [c for c in results_df.columns if 'relative_decrease' in c]
    cols_order.extend(rel_cols)
    if 'caveat' in results_df.columns:
        cols_order.append('caveat')
    
    # Filter to existing columns
    final_cols = [c for c in cols_order if c in results_df.columns]
    results_df = results_df[final_cols]

    logger.info(f"Saving results to {args.output}")
    results_df.to_csv(args.output, index=False)
    
    logger.info("Sensitivity analysis complete.")
    print(f"\nSensitivity Analysis Results saved to: {args.output}")
    print(results_df.to_string(index=False))

if __name__ == '__main__':
    main()
