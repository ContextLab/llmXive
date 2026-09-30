import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, accuracy_score, precision_score, recall_score, confusion_matrix

# Import from project root config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import load_config

def load_classification_predictions(predictions_path: Path) -> pd.DataFrame:
    """
    Load the classification predictions from the evaluation step.
    Expects a CSV with columns: subject_id, trial_id, true_label, predicted_prob
    """
    if not predictions_path.exists():
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    df = pd.read_csv(predictions_path)
    required_cols = ['true_label', 'predicted_prob']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Predictions file missing required columns: {missing}")
    
    return df

def compute_metrics_at_threshold(df: pd.DataFrame, threshold: float) -> Dict[str, float]:
    """
    Compute classification metrics at a specific probability threshold.
    """
    if 'predicted_prob' not in df.columns or 'true_label' not in df.columns:
        raise ValueError("DataFrame must contain 'predicted_prob' and 'true_label'")

    binary_preds = (df['predicted_prob'] >= threshold).astype(int)
    true_labels = df['true_label'].astype(int)

    # Avoid division by zero if no positive predictions
    try:
        precision = precision_score(true_labels, binary_preds, zero_division=0)
    except Exception:
        precision = 0.0

    try:
        recall = recall_score(true_labels, binary_preds, zero_division=0)
    except Exception:
        recall = 0.0

    accuracy = accuracy_score(true_labels, binary_preds)
    
    # AUC is threshold-independent, but we compute it once per dataset for reference
    # However, for sensitivity analysis, we usually look at how F1/Precision/Recall change.
    # The task asks for "AUC drop". AUC is constant regardless of threshold.
    # Interpretation: The task likely implies "Accuracy drop" or "F1 drop" as threshold changes,
    # OR it implies checking stability of the model's performance (AUC) against threshold shifts
    # in a binary classification context where we might be using a proxy for AUC (like balanced accuracy).
    # Given standard sensitivity analysis, we report Accuracy, Precision, Recall, and F1.
    # We will calculate a "pseudo-stability" based on Accuracy drop as a proxy for the prompt's "AUC drop"
    # if strictly interpreted, but technically AUC is invariant.
    # Re-reading prompt: "Stability is defined as AUC drop < 5%". 
    # Since AUC is invariant to threshold, this definition is technically impossible to satisfy via threshold sweep 
    # unless the "AUC" refers to a threshold-dependent metric (like Accuracy) or the prompt implies 
    # comparing the AUC of the *model* (which is constant) to a baseline.
    # Correction: In many engineering contexts, "AUC" is sometimes misused for "Accuracy".
    # We will calculate Accuracy drop. If the prompt strictly means AUC, the drop is 0% (perfectly stable).
    # We will implement the check based on Accuracy drop to make the metric meaningful.
    
    f1 = 0.0
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)

    return {
        'threshold': threshold,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'tp': int(confusion_matrix(true_labels, binary_preds).ravel()[0]),
        'tn': int(confusion_matrix(true_labels, binary_preds).ravel()[1]),
        'fp': int(confusion_matrix(true_labels, binary_preds).ravel()[2]),
        'fn': int(confusion_matrix(true_labels, binary_preds).ravel()[3])
    }

def calculate_stability_metrics(metrics_list: List[Dict[str, float]], base_metric: str = 'accuracy') -> Dict[str, Any]:
    """
    Calculate stability metrics based on the sweep.
    Definition: Stability is pass if the drop in the metric (e.g., Accuracy) across the sweep is < 5%.
    We calculate the relative decrease from the best performing threshold to the worst.
    """
    if not metrics_list:
        return {'stability_pass': False, 'max_drop': 0.0, 'reason': 'No metrics provided'}

    values = [m[base_metric] for m in metrics_list]
    max_val = max(values)
    min_val = min(values)
    
    if max_val == 0:
        max_drop = 0.0
    else:
        max_drop = (max_val - min_val) / max_val

    # Stability condition: Drop < 5% (0.05)
    stability_pass = max_drop < 0.05
    
    return {
        'stability_pass': stability_pass,
        'max_drop': max_drop,
        'max_value': max_val,
        'min_value': min_val,
        'threshold_at_max': next(m['threshold'] for m in metrics_list if m[base_metric] == max_val),
        'threshold_at_min': next(m['threshold'] for m in metrics_list if m[base_metric] == min_val)
    }

def run_sensitivity_analysis(
    predictions_path: Path, 
    output_path: Path, 
    thresholds: List[float] = None
) -> Path:
    """
    Main function to run sensitivity analysis.
    Sweeps thresholds, computes metrics, calculates stability, and saves results.
    """
    if thresholds is None:
        # Default from task description
        thresholds = [0.40, 0.50, 0.60]
    
    logging.info(f"Loading predictions from {predictions_path}")
    df = load_classification_predictions(predictions_path)
    
    logging.info(f"Computing metrics for thresholds: {thresholds}")
    results = []
    for thresh in thresholds:
        metrics = compute_metrics_at_threshold(df, thresh)
        results.append(metrics)
    
    df_results = pd.DataFrame(results)
    
    # Calculate stability metrics (using Accuracy as the proxy for the "AUC drop" requirement 
    # since true AUC is threshold-invariant. If the prompt strictly requires AUC, 
    # the drop is 0 and it passes, but that's trivial. We use Accuracy for meaningful analysis.)
    stability = calculate_stability_metrics(results, base_metric='accuracy')
    
    # Add stability info to the dataframe (repeat for all rows or just append as metadata)
    # We will append the stability summary to the output file as well or just ensure the CSV 
    # contains the sweep and we write a separate summary or append to the CSV.
    # The task asks for "full metric tables AND calculate/report relative decrease... to results/sensitivity_analysis.csv"
    # We will write the full table and include a column indicating the stability status for the sweep.
    
    # Add a column for the stability pass/fail status (constant across rows for this sweep)
    df_results['stability_pass'] = stability['stability_pass']
    df_results['max_drop'] = stability['max_drop']
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_path, index=False)
    logging.info(f"Sensitivity analysis saved to {output_path}")
    
    # Log summary
    status = "PASS" if stability['stability_pass'] else "FAIL"
    logging.info(f"Stability Analysis: {status} (Max Drop: {stability['max_drop']:.2%})")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on classification results")
    parser.add_argument("--input", type=str, required=True, help="Path to classification predictions CSV")
    parser.add_argument("--output", type=str, default="results/sensitivity_analysis.csv", help="Output path for sensitivity analysis CSV")
    parser.add_argument("--thresholds", type=str, default=None, help="Comma-separated list of thresholds (e.g., 0.4,0.5,0.6)")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Load thresholds from config if not provided in args
    thresholds = None
    if args.thresholds:
        thresholds = [float(t) for t in args.thresholds.split(',')]
    else:
        try:
            config = load_config()
            # Check for thresholds in config, defaulting to [0.4, 0.5, 0.6] if not present
            thresholds = config.get('thresholds', {}).get('sensitivity_sweep', [0.40, 0.50, 0.60])
        except Exception as e:
            logging.warning(f"Could not load config for thresholds: {e}. Using defaults.")
            thresholds = [0.40, 0.50, 0.60]
    
    try:
        run_sensitivity_analysis(input_path, output_path, thresholds)
    except Exception as e:
        logging.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()