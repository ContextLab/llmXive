import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
import yaml

# Add parent directory to path to allow imports from sibling modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from classification.evaluate import load_held_out_data, compute_metrics
from config import load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_classification_predictions(config_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the labeled data and predictions from the classification pipeline.
    Assumes T029 and T030 have run and produced the necessary artifacts.
    """
    # Expected paths based on project structure and previous tasks
    labeled_data_path = config_path.parent / "data" / "processed" / "labeled_data.csv"
    metrics_path = config_path.parent / "results" / "classification_metrics.csv"
    
    if not labeled_data_path.exists():
        raise FileNotFoundError(f"Labeled data not found at {labeled_data_path}. "
                                "Ensure T029 has run successfully.")
    
    if not metrics_path.exists():
        raise FileNotFoundError(f"Classification metrics not found at {metrics_path}. "
                                "Ensure T030 has run successfully.")
    
    # Load the labeled data which contains ground truth and predictions
    df = pd.read_csv(labeled_data_path)
    
    # Load existing metrics to verify schema
    existing_metrics = pd.read_csv(metrics_path)
    
    return df, existing_metrics

def compute_metrics_at_threshold(df: pd.DataFrame, threshold: float) -> Dict[str, float]:
    """
    Compute accuracy and AUC for a specific probability threshold.
    Expects columns 'probability' (predicted score) and 'label' (ground truth).
    """
    if 'probability' not in df.columns or 'label' not in df.columns:
        raise ValueError("DataFrame must contain 'probability' and 'label' columns.")
    
    # Convert probability to binary prediction based on threshold
    df['prediction'] = (df['probability'] >= threshold).astype(int)
    
    # Compute metrics
    metrics = compute_metrics(df, 'label', 'prediction')
    
    return {
        'accuracy': metrics.get('accuracy', 0.0),
        'auc': metrics.get('auc', 0.0)
    }

def calculate_stability_metrics(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate stability metrics across the threshold sweep.
    Stability is defined as AUC drop < 5% across the threshold sweep.
    """
    if not results:
        return []
    
    # Sort results by threshold to ensure correct ordering
    results_sorted = sorted(results, key=lambda x: x['threshold'])
    
    # Extract AUC values
    auc_values = [r['auc'] for r in results_sorted]
    max_auc = max(auc_values)
    min_auc = min(auc_values)
    
    # Calculate relative decrease
    if max_auc > 0:
        relative_decrease = (max_auc - min_auc) / max_auc
    else:
        relative_decrease = 0.0
    
    # Determine stability status (AUC drop < 5%)
    stability_pass = relative_decrease < 0.05
    stability_status = "PASS" if stability_pass else "FAIL"
    
    # Add stability status to each result
    for r in results_sorted:
        r['stability_status'] = stability_status
        r['relative_decrease'] = relative_decrease
    
    return results_sorted

def run_sensitivity_analysis(config_path: Path, output_path: Path) -> None:
    """
    Main function to run sensitivity analysis across defined thresholds.
    """
    logger.info(f"Loading configuration from {config_path}")
    config = load_config(config_path)
    
    # Get thresholds from config, defaulting to {0.40, 0.50, 0.60}
    thresholds = config.get('thresholds', [0.4, 0.5, 0.6])
    if not thresholds:
        thresholds = [0.4, 0.5, 0.6]
        logger.warning("No thresholds found in config, using defaults: [0.4, 0.5, 0.6]")
    
    logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
    
    # Load data
    df, _ = load_classification_predictions(config_path)
    
    # Compute metrics for each threshold
    results = []
    for thresh in thresholds:
        logger.info(f"Computing metrics for threshold {thresh}")
        try:
            metrics = compute_metrics_at_threshold(df, thresh)
            results.append({
                'threshold': thresh,
                'accuracy': metrics['accuracy'],
                'auc': metrics['auc']
            })
        except Exception as e:
            logger.error(f"Error computing metrics for threshold {thresh}: {e}")
            results.append({
                'threshold': thresh,
                'accuracy': np.nan,
                'auc': np.nan
            })
    
    # Calculate stability metrics
    results_with_stability = calculate_stability_metrics(results)
    
    # Create DataFrame and save
    df_results = pd.DataFrame(results_with_stability)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis results saved to {output_path}")
    
    # Print summary
    print("\n--- Sensitivity Analysis Summary ---")
    print(df_results.to_string(index=False))
    print(f"Stability Status: {df_results['stability_status'].iloc[0]}")
    print(f"Max AUC: {df_results['auc'].max():.4f}")
    print(f"Min AUC: {df_results['auc'].min():.4f}")
    print(f"Relative Decrease: {df_results['relative_decrease'].iloc[0]:.4f}")
    print("------------------------------------")

def main():
    parser = argparse.ArgumentParser(description='Run sensitivity analysis on classification thresholds')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--output', type=str, default='results/sensitivity_analysis.csv', help='Output CSV path')
    args = parser.parse_args()
    
    config_path = Path(args.config)
    output_path = Path(args.output)
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    run_sensitivity_analysis(config_path, output_path)

if __name__ == "__main__":
    main()
