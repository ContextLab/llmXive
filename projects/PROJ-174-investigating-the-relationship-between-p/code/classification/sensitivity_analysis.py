import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_config
from classification.evaluate import load_held_out_data, compute_metrics

def load_classification_predictions(path: str = None) -> pd.DataFrame:
    """
    Load the classification results (predictions + ground truth) from disk.
    Expected file: data/processed/classification_results.csv (or similar).
    Falls back to looking in results/ if not found in processed.
    """
    if path is None:
        # Try standard locations based on project structure
        processed_path = Path("data/processed/classification_results.csv")
        results_path = Path("results/classification_results.csv")
        
        if processed_path.exists():
            path = str(processed_path)
        elif results_path.exists():
            path = str(results_path)
        else:
            raise FileNotFoundError(
                f"Could not find classification results at expected paths: "
                f"{processed_path} or {results_path}"
            )
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Classification results file not found: {path}")
    
    df = pd.read_csv(path)
    
    # Verify required columns exist
    required_cols = ['prediction', 'truth'] # Assuming these are the columns from T030
    # If column names differ (e.eg 'label', 'predicted'), we might need to adapt.
    # Based on T030 (evaluate.py), we assume 'prediction' and 'truth' or similar.
    # Let's be robust: check for any binary columns.
    if 'prediction' not in df.columns:
        if 'predicted' in df.columns:
            df['prediction'] = df['predicted']
        else:
            raise ValueError("Column 'prediction' (or 'predicted') not found in results.")
    
    if 'truth' not in df.columns:
        if 'label' in df.columns:
            df['truth'] = df['label']
        else:
            raise ValueError("Column 'truth' (or 'label') not found in results.")
    
    return df

def compute_metrics_at_threshold(df: pd.DataFrame, threshold: float) -> Dict[str, float]:
    """
    Compute accuracy, precision, recall, and AUC at a specific probability threshold.
    Assumes 'prediction' column contains probabilities (0-1).
    Converts probabilities to binary class based on threshold.
    """
    # Ensure we have the raw probabilities
    # If the input file already has binary predictions, we might need to re-read raw scores
    # For this implementation, we assume the input file has a 'probability' or 'score' column.
    # If not, we assume 'prediction' IS the probability.
    
    if 'probability' in df.columns:
        probs = df['probability'].values
    elif 'score' in df.columns:
        probs = df['score'].values
    else:
        # Fallback: if 'prediction' is already binary, we can't compute AUC properly
        # without the raw scores. We will assume 'prediction' is the probability for now.
        # If T030 output binary, this task might need the raw scores file.
        # Let's assume T030 saved the raw probabilities in a column named 'probability'
        # or 'prediction' is the probability.
        if df['prediction'].dtype == float:
            probs = df['prediction'].values
        else:
            raise ValueError("Cannot compute AUC without probability scores. "
                             "Ensure 'probability', 'score', or float 'prediction' column exists.")
    
    truths = df['truth'].values
    
    # Apply threshold
    binary_preds = (probs >= threshold).astype(int)
    
    # Calculate metrics
    tp = np.sum((binary_preds == 1) & (truths == 1))
    tn = np.sum((binary_preds == 0) & (truths == 0))
    fp = np.sum((binary_preds == 1) & (truths == 0))
    fn = np.sum((binary_preds == 0) & (truths == 1))
    
    accuracy = (tp + tn) / len(truths) if len(truths) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # Calculate AUC manually (trapezoidal rule) or use sklearn if available
    # Since sklearn is in requirements, we can use it for robust AUC
    try:
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(truths, probs)
    except ImportError:
        # Fallback manual calculation if sklearn missing (unlikely per requirements)
        # Sort by probability descending
        sorted_indices = np.argsort(-probs)
        sorted_truths = truths[sorted_indices]
        sorted_probs = probs[sorted_indices]
        
        # Calculate TPR and FPR at each point
        total_pos = np.sum(truths == 1)
        total_neg = np.sum(truths == 0)
        
        if total_pos == 0 or total_neg == 0:
            auc = 0.5 # Undefined or neutral
        else:
            tpr = np.cumsum(sorted_truths) / total_pos
            fpr = np.cumsum(1 - sorted_truths) / total_neg
            
            # Add (0,0) point
            fpr = np.concatenate([[0], fpr])
            tpr = np.concatenate([[0], tpr])
            
            # Trapezoidal rule
            auc = np.trapz(tpr, fpr)
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'auc': auc
    }

def calculate_stability_metrics(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate stability status based on AUC drop across thresholds.
    Stability is defined as AUC drop < 5% across the threshold sweep.
    """
    if not results:
        return results
    
    # Sort by threshold
    sorted_results = sorted(results, key=lambda x: x['threshold'])
    
    # Find max and min AUC
    aucs = [r['auc'] for r in sorted_results]
    max_auc = max(aucs)
    min_auc = min(aucs)
    
    # Calculate relative decrease
    if max_auc > 0:
        relative_decrease = (max_auc - min_auc) / max_auc
    else:
        relative_decrease = 0.0
    
    # Stability status: Pass if relative decrease < 0.05 (5%)
    stable = relative_decrease < 0.05
    stability_status = "PASS" if stable else "FAIL"
    
    # Update each result with the overall stability status and relative decrease
    for r in sorted_results:
        r['relative_decrease'] = relative_decrease
        r['stability_status'] = stability_status
    
    return sorted_results

def run_sensitivity_analysis():
    """
    Main entry point for sensitivity analysis.
    Loads config, sweeps thresholds, computes metrics, and saves results.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Get thresholds from config or use defaults
    thresholds = config.get('thresholds', [0.40, 0.50, 0.60])
    if not thresholds:
        thresholds = [0.40, 0.50, 0.60]
    
    logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
    
    # Load classification results
    try:
        df = load_classification_predictions()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Compute metrics for each threshold
    results = []
    for thresh in thresholds:
        logger.info(f"Computing metrics for threshold {thresh}")
        metrics = compute_metrics_at_threshold(df, thresh)
        results.append({
            'threshold': thresh,
            **metrics
        })
    
    # Calculate stability
    results = calculate_stability_metrics(results)
    
    # Prepare output DataFrame
    output_df = pd.DataFrame(results)
    # Ensure columns are in correct order: threshold, accuracy, auc, stability_status
    # Plus relative_decrease for transparency
    cols = ['threshold', 'accuracy', 'auc', 'relative_decrease', 'stability_status']
    # Filter to only existing columns if any are missing (shouldn't happen)
    output_df = output_df[[c for c in cols if c in output_df.columns]]
    
    # Save to results/sensitivity_analysis.csv
    output_path = Path("results/sensitivity_analysis.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    
    # Print summary
    print(f"\nSensitivity Analysis Summary:")
    print(f"Thresholds tested: {thresholds}")
    print(f"Stability Status: {results[0]['stability_status']}")
    print(f"Max AUC: {max(r['auc'] for r in results):.4f}")
    print(f"Min AUC: {min(r['auc'] for r in results):.4f}")
    print(f"Relative Decrease: {results[0]['relative_decrease']*100:.2f}%")
    
    return output_df

def main():
    parser = argparse.ArgumentParser(description="Run sensitivity analysis for classification thresholds")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    args = parser.parse_args()
    
    # Override config path if provided (though load_config usually handles default)
    # The load_config function in code/config.py likely reads from a fixed path or env.
    # We assume the standard path for now.
    run_sensitivity_analysis()

if __name__ == "__main__":
    main()